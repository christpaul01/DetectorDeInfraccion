import datetime

import os
import tkinter as tk
from collections import defaultdict
from tkinter import filedialog

from jupyter_client.consoleapp import classes
from sympy.categories import Object
from torch.nn.functional import threshold
# import for yolo model
from ultralytics import YOLO
import cv2
import numpy as np
import time
import torch
import ast
import base64
from PIL import Image

# For Streaming Video
from django.http import StreamingHttpResponse

from .models import Camara, Direccion, ROI, TipoVehiculo, Umbral


def get_camaras():
    """
    Obtiene todas las cámaras de la base de datos.

    Returns:
        QuerySet: Un QuerySet con todas las cámaras.
    """
    return Camara.objects.all()


def is_inside_trapezoid(point, roi_vertices):
    # point is the center point (x, y) of the bounding box
    # roi_vertices are the vertices of the trapezoid ROI
    return cv2.pointPolygonTest(np.array(roi_vertices, dtype=np.int32), point, False) >= 0

def start_vehicle_detection(id_camara):
    camara = Camara.objects.get(id_camara=id_camara)
    nombre = camara.nombre_camara
    url_input = camara.url_camara
    track_history = defaultdict(list)
    # Initialize variables for frame processing time
    processing_start_time = time.time()
    processing_end_time = time.time()

    vehicles = TipoVehiculo.objects.all().values_list('id_tipo_vehiculo', flat=True)
    if vehicles is None:
        # Default vehicles
        vehicles = [2,3,5,7]

    # Obtener el umbral de detección de vehículos desde la base de datos
    threshold_vehicle = camara.threshold_vehicle
    if threshold_vehicle is None:
        # Si no hay umbral en la cámara, buscar en la tabla de umbrales, FALLBACKS
        threshold_vehicle = Umbral.objects.filter(nombre_umbral='Threshold_Vehicle').first().valor_umbral
        if threshold_vehicle is None:
            threshold_vehicle = 0.55  # Umbral por defecto

    print(f"Trying to start detection from camera: {nombre}, url: {url_input}")

    # Check if the system has a CUDA GPU available

    if torch.cuda.is_available():
        # CUDA GPU available
        print("CUDA enabled")
        torch.cuda.set_device(0)
    else:
        print("Running on CPU")

    # Get the absolute path of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to the model file
    helmet_model_path = os.path.join(script_dir, './modelos/best.pt')

    # Check if the file exists
    if not os.path.exists(helmet_model_path):
        print(f"Error: No se encontró el archivo {helmet_model_path}")
    else:
        print(f"Archivo encontrado: {helmet_model_path}")



    # Load YOLO models
    model = YOLO('yolo11s.pt')

    cap = cv2.VideoCapture(url_input)
    ret, frame = cap.read()
    # Get the video frame dimensions and frame rate
    W, H, input_fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
    # Calculate the time between frames to process
    frame_time = 1 / input_fps
    frame_num = 0

    # Load ROIs
    roi_vertices = [(0, 0), (W, 0), (W, H), (0, H)]  # Default values in case no ROI found
    p_roi_vertices = [(0, 0), (W, 0), (W, H), (0, H)]  # Default prohibited ROI

    try:
        roi_coordinates = ast.literal_eval(ROI.objects.get(id_camara=id_camara, tipo_roi='N').coordenadas)
        roi_vertices = [(x, y) for x, y in roi_coordinates]
    except ROI.DoesNotExist:
        print("ROI not found, using default values")

    try:
        p_roi_coordenadas = ast.literal_eval(ROI.objects.get(id_camara=id_camara, tipo_roi='P').coordenadas)
        p_roi_vertices = [(x, y) for x, y in p_roi_coordenadas]
    except ROI.DoesNotExist:
        print("Prohibited ROI not found, using default values")

    crossed_vehicles = set()  # Track vehicles that have crossed

    while cap.isOpened():
        success, frame = cap.read()
        if success:
            frame_num += 1
            processing_start_time = time.time()

            results = model.track(frame, persist=True, classes = vehicles, tracker="bytetrack.yaml")

            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xywh.cpu().numpy().astype(int)
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                scores = results[0].boxes.conf.cpu().numpy()

                annotated_frame = results[0].plot()

                for box, track_id, score in zip(boxes, track_ids, scores):
                    x, y, w, h = box
                    center_point = (int(x + w / 2), int(y + h / 2))

                    if score >= threshold_vehicle:
                        # Check if vehicle is inside the normal ROI
                        if is_inside_trapezoid(center_point, roi_vertices):
                            # Store that this vehicle has been inside the normal ROI
                            track_history[track_id].append("N")

                    # Check if the vehicle is now inside the prohibited ROI
                    if is_inside_trapezoid(center_point, p_roi_vertices):
                        # If the vehicle was previously in the normal ROI and now in the prohibited ROI
                        if "N" in track_history[track_id] and track_id not in crossed_vehicles:
                            print(f"El Vehiculo {track_id} cruzo desde el ROI Normal hacia el ROI Prohibido!")
                            crossed_vehicles.add(track_id)  # Mark the vehicle as crossed

                # Draw the ROIs on the frame for visualization
                cv2.polylines(annotated_frame, [np.array(roi_vertices, dtype=np.int32)], isClosed=True, color=(255, 0, 0), thickness=2)
                cv2.polylines(annotated_frame, [np.array(p_roi_vertices, dtype=np.int32)], isClosed=True, color=(0, 0, 255), thickness=2)



                # NOTE: METRICS FOR VEHICLE DETECTION
                # Get the elapsed time for processing the frame
                processing_end_time = time.time()

                # Calculate the elapsed time for processing the frame
                elapsed_time_frame = processing_end_time - processing_start_time
                # Calculate the output frame rate
                output_frame_rate = 1 / elapsed_time_frame
                # Calculate the ratio of the output frame rate to the input frame rate
                frame_rate_ratio = output_frame_rate / input_fps

                # Print the frame rate and elapsed time for each frame
                print("Frame rate: {:.2f} frames per second".format(output_frame_rate))
                # Results should be above 1 to keep up with the frame rate
                print("Output/Input fps ratio: {:.2f}x".format(frame_rate_ratio))
                print(f"Elapsed time: {elapsed_time_frame} seconds for frame #{frame_num}")

                # TODO: Borrar esta parte del codigo en produccion
                # Show the frame
                cv2.imshow(f"YOLOv8 Tracking for {nombre}", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            break

    cap.release()
    cv2.destroyAllWindows()



def video_to_html(video_path, start_frame, end_frame, playback_speed=None):
    try:
        # Load the video
        cap = cv2.VideoCapture(video_path)

        # Check if the video is opened successfully
        if not cap.isOpened():
            raise ValueError(f"Error opening video file: {video_path}")

        # Get total number of frames and FPS in the video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Ensure end_frame does not exceed the total number of frames
        end_frame = min(end_frame, total_frames - 1)

        # Set the video to start from the start_frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Default playback speed is based on the video's FPS
        if playback_speed is None:
            playback_speed = 1 / fps

        current_frame = start_frame

        while current_frame <= end_frame:
            ret, frame = cap.read()

            if not ret:
                print(f"Error reading frame {current_frame}")
                break

            # Encode the frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print(f"Error encoding frame {current_frame}")
                continue

            frame_bytes = buffer.tobytes()

            # Yield the frame as part of an HTTP response, simulating streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Mimic video playback speed
            time.sleep(playback_speed)

            current_frame += 1

    except Exception as e:
        print(f"Exception occurred: {e}")

    finally:
        cap.release()
        cv2.destroyAllWindows()


def watch_video_from_frame(video_path, start_frame, end_frame):
    # Load the video
    cap = cv2.VideoCapture(video_path)

    # Check if the video is opened successfully
    if not cap.isOpened():
        print("Error opening video file")
        return

    # Get total number of frames in the video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Ensure end_frame does not exceed the total number of frames
    end_frame = min(end_frame, total_frames - 1)

    # Create a single window for the video playback
    cv2.namedWindow("Video Playback", cv2.WINDOW_NORMAL)

    # Start a loop to continuously play the video from start_frame to end_frame
    while True:
        # Set the video to start from the start_frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Read and display frames from start_frame to end_frame
        current_frame = start_frame
        while current_frame <= end_frame:
            ret, frame = cap.read()

            if not ret:
                print("Error reading frame. Rewinding to start.")
                break  # Break the loop if there's an error reading the frame

            # Display the current frame in the same window
            cv2.imshow("Video Playback", frame)

            # Wait for a short period between frames (25 ms) to mimic normal video playback speed
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return  # Exit if 'q' is pressed

            # Move to the next frame
            current_frame += 1

        # Once end_frame is reached, the loop continues, resetting to start_frame

    # Release the video capture object and close all windows
    cap.release()
    cv2.destroyAllWindows()

def check_models_existence():
    """
    Verifica si los archivos de los modelos existen en el sistema de archivos.

    Args:
        camara (Camara): La cámara de la que se verificarán los archivos.

    Returns:
        bool: True si los archivos existen, False en caso contrario.
    """
    # Rutas de los archivos de los modelos
    yolov8s_model_path = "../modelos/yolov8s.pt"
    LP_model_path = "../modelos/matriculas.pt"
    helmet_model_path = "../modelos/cascos.pt"

    # Verificar si los archivos existen
    if not os.path.exists(yolov8s_model_path):
        print("Error: No se encontró el archivo yolov8s.pt")
        return False

    if not os.path.exists(LP_model_path):
        print("Error: No se encontró el archivo matriculas.pt")
        return False

    if not os.path.exists(helmet_model_path):
        print("Error: No se encontró el archivo cascos.pt")
        return False

    return True


def check_camara_files_integrity(camara):
    """
    Verifica si los archivos de la cámara existen en el sistema de archivos.

    Args:
        camara (Camara): La cámara de la que se verificarán los archivos.

    Returns:
        bool: True si los archivos existen y se puedan leer, False en caso contrario.
    """
    # Rutas de los archivos de la cámara
    video_path = camara.url_camara
    try:
        roi = ROI.objects.get(id_camara=camara.id_camara).coordenadas
    except ROI.DoesNotExist:
        roi = None

    # Verificar si los archivos existen
    if not os.path.exists(video_path):
        print(f"Error: No se encontró el archivo de video en la ruta {video_path}")
        return False
    else:
        try:
            # Open the video file
            cap = cv2.VideoCapture(video_path)
            # Check if camera or video opened successfully
            ret, frame = cap.read()
            # close the video file
            cap.release()
        except:
            print("Error: No se pudo abrir el archivo de video.")
            return False

    return True


def get_time_from_seconds(seconds):
    """
    Convierte una cantidad de segundos a una cadena de texto en formato HH:MM:SS.

    Args:
        seconds (int): La cantidad de segundos.

    Returns:
        str: Una cadena de texto en formato HH:MM:SS.
    """
    return str(datetime.timedelta(seconds=seconds))


import cv2
import numpy as np

def get_video_info(video_path, resize_factor=0.25):
    """
    Obtiene la resolución (ancho y alto), los FPS y una vista previa del primer fotograma de un archivo de video,
    redimensionando el fotograma para que sea más pequeño.

    Args:
        video_path (str): La ruta del archivo de video.
        resize_factor (float): Factor de redimensionamiento para reducir el tamaño del fotograma.

    Returns:
        tuple: Una tupla que contiene (ancho, alto, fps, frame_count, video_length, first_frame) o None si no se puede abrir el video.
    """
    # Abre el archivo de video
    cap = cv2.VideoCapture(video_path)

    # Verifica si se pudo abrir el video
    if not cap.isOpened():
        print(f"Error: No se pudo abrir el video en la ruta {video_path}")
        return None

    # Obtener la resolución (ancho y alto)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Obtener los FPS
    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    if fps == 0:
        print("Error: No se pudo obtener los FPS del video.")
        video_length = 0
    else:
        video_length = frame_count / fps

    # Leer el primer fotograma
    ret, first_frame = cap.read()
    if not ret:
        print("Error: No se pudo leer el primer fotograma.")
        first_frame = None
    else:
        # Redimensionar el fotograma
        new_width = int(frame_width * resize_factor)
        new_height = int(frame_height * resize_factor)
        first_frame = cv2.resize(first_frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

    # Liberar el recurso del video
    cap.release()

    # Retornar la información
    return frame_width, frame_height, fps, frame_count, video_length, first_frame

def frame_to_base64(frame):
    # Encode the frame as a JPEG image
    _, buffer = cv2.imencode('.jpg', frame)
    # Convert the buffer to a Base64 string
    return base64.b64encode(buffer).decode('utf-8')

def save_first_frame(camara_instance, first_frame):
    # Convert the first frame to Base64
    base64_frame = frame_to_base64(first_frame)

    # Save the Base64 string to the Camara instance
    camara_instance.first_frame_base64 = base64_frame
    camara_instance.save()


def get_frame_from_video (video_path):
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if not ret:
        print("Error reading video.")
        exit()
    return frame

def calculate_angle(x1, y1, x2, y2):
    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
    print(angle)
    return abs(angle)

def get_roi_vertices(frame, window_name="Select ROI"):
    """
    Permite al usuario seleccionar un ROI en una ventana de OpenCV.

    Args:
        frame (numpy.ndarray): La imagen en la que se seleccionará el ROI.
        window_name (str): El nombre de la ventana de OpenCV.

    Returns:
        list: Una lista de las coordenadas de los vértices del ROI.
    """
    # Copiar la imagen para no modificar la original
    img = frame.copy()

    # Crear una lista para almacenar los vértices del ROI
    roi_vertices = []
    max_vertices = 4
    global num_pressed
    max_angle = 50
    num_pressed = 0
    roi_selected = False

    # Función para manejar los eventos del mouse
    def mouse_callback(event, x, y, flags, param):
        global num_pressed
        if (event == cv2.EVENT_LBUTTONDOWN) and num_pressed <= max_vertices:
            num_pressed += 1
            roi_vertices.append((x, y))
            roi_selected = False

        elif event == cv2.EVENT_LBUTTONUP and num_pressed <= max_vertices:
            if roi_vertices[num_pressed - 1] != (x, y):
                num_pressed += 1
                print(num_pressed)
                roi_vertices.append((x, y))
                if (num_pressed == 2):
                    angle = calculate_angle(roi_vertices[0][0], roi_vertices[0][1], roi_vertices[1][0],
                                            roi_vertices[1][1])
                    if (angle > max_angle):
                        roi_vertices.remove(roi_vertices[1])
                        roi_vertices.remove(roi_vertices[0])
                        num_pressed -= 2
                    print(angle)
                if (num_pressed == 4):
                    angle = calculate_angle(roi_vertices[2][0], roi_vertices[2][1], roi_vertices[3][0],
                                            roi_vertices[3][1])
                    if (angle > max_angle):
                        roi_vertices.remove(roi_vertices[3])
                        roi_vertices.remove(roi_vertices[2])
                        num_pressed -= 2
                    print(angle)
            else:
                roi_vertices.remove(roi_vertices[num_pressed - 1])
                num_pressed -= 1
            if num_pressed == max_vertices:
                # Verify that the order of the vertices is correct, if not, swap them
                if roi_vertices[0][0] - roi_vertices[1][0] < 0 < roi_vertices[3][0] - roi_vertices[2][0]:
                    roi_vertices[2], roi_vertices[3] = roi_vertices[3], roi_vertices[2]

            for i in range(len(roi_vertices)):
                print(roi_vertices[i])
            roi_selected = True
            # Draw the trapezoid on the frame
            cv2.polylines(img, [np.array(roi_vertices)], isClosed=True, color=(0, 255, 0), thickness=2)
            cv2.putText(img, 'ROI: {}'.format(roi_vertices), (roi_vertices[0][0], roi_vertices[0][1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 210), 2, cv2.LINE_AA)
            cv2.imshow(window_name, img)

    # Crear una ventana de OpenCV y mostrar la imagen
    cv2.namedWindow(window_name)
    cv2.imshow(window_name, img)

    # Asignar la función de callback al evento del mouse
    cv2.setMouseCallback(window_name, mouse_callback)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    if roi_selected:
        return roi_vertices

    # # Esperar a que el usuario seleccione los vértices del ROI
    # while len(roi_vertices) < 4:
    #     key = cv2.waitKey(1) & 0xFF
    #
    #     # Salir si se presiona la tecla 'q'
    #     if key == ord('q'):
    #         break

    # Cerrar la ventana de OpenCV
    cv2.destroyAllWindows()

    return roi_vertices

def get_dominant_color(pil_img):
    """
    Returns the dominant color of an image as an RGB tuple.

    Args:
    - pil_img (PIL.Image): The PIL image from which to detect the color.

    Returns:
    - tuple: Dominant RGB color in the form (R, G, B).
    """
    img = pil_img.copy()
    img = img.convert("RGB")
    img = img.resize((1, 1), resample=0)  # Resize to 1x1 pixel for dominant color
    dominant_color = img.getpixel((0, 0))
    return dominant_color

def detect_roi_dominant_color(image, vertices):
    """
    Detects the dominant color within the specified polygonal ROI in the image.

    Args:
    - image (np.array): The image frame where detection will be applied.
    - vertices (list of tuples): List of (x, y) coordinates defining the vertices of the polygonal ROI.

    Returns:
    - str: RGB color in text format (e.g., "RGB(255, 0, 0)").
    """

    # Create a mask for the polygonal ROI
    mask = np.zeros_like(image[:, :, 0])
    cv2.fillPoly(mask, [np.array(vertices, np.int32)], 255)

    # Get bounding box of the polygon to crop the masked region
    x, y, w, h = cv2.boundingRect(np.array(vertices))
    cropped_image = image[y:y+h, x:x+w]
    cropped_mask = mask[y:y+h, x:x+w]

    # Apply the mask to the cropped image to get only the ROI region
    roi_image = cv2.bitwise_and(cropped_image, cropped_image, mask=cropped_mask)

    # Convert the masked ROI region to a PIL image
    pil_image = Image.fromarray(cv2.cvtColor(roi_image, cv2.COLOR_BGR2RGB))

    # Get the dominant color in the ROI
    dominant_color = get_dominant_color(pil_image)

    # Format as RGB text
    rgb_text = f"RGB{dominant_color}"
    print(f"Detected RGB color: {rgb_text}")

    return rgb_text

def is_red_or_pink(rgb_text):
    """
    Determines if the RGB color in text format is within the red or pink color range,
    so it can properly identify when the traffic lights is red given any situation
    (night or day).

    Args:
    - rgb_text (str): RGB color in text format (e.g., "RGB(255, 0, 0)").

    Returns:
    - bool: True if the color is within the red/pink range, False otherwise.
    """

    # Parse RGB values from the text format
    rgb_values = rgb_text.strip("RGB()").split(", ")
    r, g, b = int(rgb_values[0]), int(rgb_values[1]), int(rgb_values[2])

    # Define the red/pink color range, including very light shades
    is_red_or_pink = (
        200 <= r <= 255 and      # High red values
        0 <= g <= 255 and        # Expanded green range to include lighter shades
        0 <= b <= 255            # Expanded blue range to include lighter shades
    )

    return is_red_or_pink

