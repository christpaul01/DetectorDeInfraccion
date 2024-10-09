import datetime

import os
import tkinter as tk
from collections import defaultdict
from tkinter import filedialog

# import for yolo model
from ultralytics import YOLO
import cv2
import numpy as np
import time
import torch
import ast
import base64

# For Streaming Video
from django.http import StreamingHttpResponse

from .models import Camara, Direccion, ROI


def get_camaras():
    """
    Obtiene todas las cámaras de la base de datos.

    Returns:
        QuerySet: Un QuerySet con todas las cámaras.
    """
    return Camara.objects.all()


def is_inside_trapezoid(box, roi_vertices):
    # box is an object bounding box as (x, y, w, h)
    # roi_vertices are the vertices of the trapezoid ROI
    x, y, w, h = box

    # Convert box to polygon
    poly = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]])

    # Check if poly is inside ROI polygon
    is_inside = cv2.pointPolygonTest(np.array(roi_vertices, dtype=np.int32), (int(x + w / 2), int(y + h / 2)),
                                     False) >= 0


def start_detection(id_camara):
    camara = Camara.objects.get(id_camara=id_camara)
    nombre = camara.nombre_camara
    url_input = camara.url_camara

    print(f"Trying to start detection from camera: {nombre}, url: {url_input}")

    # TODO: Check why this is not working
    # if not check_camara_files_integrity(camara):
    #     return

    # Carga de modelos
    #yolov8s_model_path = "./modelos/yolov8s.pt"

    # Get the absolute path of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to the model file
    LP_model_path = os.path.join(script_dir, './modelos/matriculas.pt')
    helmet_model_path = os.path.join(script_dir, './modelos/best.pt')

    # Check if the file exists
    if not os.path.exists(LP_model_path):
        print(f"Error: No se encontró el archivo {LP_model_path}")
    else:
        print(f"Archivo encontrado: {LP_model_path}")

    if not os.path.exists(helmet_model_path):
        print(f"Error: No se encontró el archivo {helmet_model_path}")
    else:
        print(f"Archivo encontrado: {helmet_model_path}")


    model = YOLO('yolov8n.pt')
    custom_LP_Model = YOLO(LP_model_path)
    custom_H_Model = YOLO(helmet_model_path)

    # TODO: Adjust manually in web interface
    # Thresholds
    thresholdVehicle = 0.5
    thresholdLicensePlate = 0.4
    thresholdHelmet = 0.7

    # Vehicles = Car, motorcycle, bus, truck
    vehicles = [2, 3, 5, 7]
    # Helmets = With Helmet, Without helmet
    helmets = [0, 1]

    # Check if the system has a CUDA GPU available

    if torch.cuda.is_available():
        # CUDA GPU available
        print("CUDA enabled")
        torch.cuda.set_device(0)
    else:
        print("Running on CPU")

    # Open the video file
    cap = cv2.VideoCapture(url_input)
    # Check if camera or video opened successfully
    ret, frame = cap.read()
    # Get the video frame dimensions
    H, W, _ = frame.shape

    print(f"Starting detection from camera: {nombre}, url: {url_input}")

    try:
        print("Getting ROI")
        roi_coordinates = ROI.objects.get(id_camara=id_camara, tipo_roi='N').coordenadas
        # Convert the string representation to a list
        roi_coordinates = ast.literal_eval(roi_coordinates)
        roi_vertices = [(x, y) for x, y in roi_coordinates]
    except ROI.DoesNotExist:
        print("ROI not found, using default values")
        roi_coordinates = [(0, 0), (W, 0), (W, H), (0, H)]

    try:
        print("Getting Prohibited ROI")
        p_roi_coordenadas = ROI.objects.get(id_camara=id_camara, tipo_roi='P').coordenadas
        # Convert the string representation to a list
        p_roi_coordenadas = ast.literal_eval(p_roi_coordenadas)
        p_roi_vertices = [(x, y) for x, y in p_roi_coordenadas]
    except ROI.DoesNotExist:
        print("Prohibited ROI not found, using default values")
        p_roi_vertices = [(0, 0), (W, 0), (W, H), (0, H)]

    video_path_out = '{}_out.mp4'.format(url_input)
    # Create a video writer object to save the output video in a MP4 file
    out = cv2.VideoWriter(video_path_out, cv2.VideoWriter_fourcc(*'MP4V'), int(cap.get(cv2.CAP_PROP_FPS)), (W, H))

    # Store the track history
    track_history = defaultdict(lambda: [])

    # Store the previous frame's bounding boxes and their corresponding IDs
    prev_boxes = []
    prev_track_ids = []

    # Store the IDs of vehicles that have crossed from ROI to prohibited ROI
    crossed_vehicles = set()



    # TODO: Usar solamente para evaluacion de funcion
    # TODO: open watch_video_from_frame in a thread to avoid blocking the main thread
    # watch_video_from_frame(url, 0, 100)

    # Loop through the video frames
    while cap.isOpened():
        # Read a frame from the video
        success, frame = cap.read()

        if success:

            # Run YOLOv8 tracking on the frame, persisting tracks between frames
            results = model.track(frame, persist=True, classes=vehicles, tracker="bytetrack.yaml")

            if results[0].boxes.id is not None:
                # Get the boxes and track IDs
                boxes = results[0].boxes.xywh.cpu().numpy().astype(int)
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)

                # Visualize the results on the frame
                annotated_frame = results[0].plot()

                results_H_custom = custom_H_Model(frame)[0]

                for result in results_H_custom.boxes.data.tolist():
                    x1, y1, x2, y2, score, class_id = result
                    helmet_box = (x1, y1, x2, y2)
                    # check if the bounding box is within the ROI
                    if is_inside_trapezoid(helmet_box, roi_vertices):
                        if score > thresholdHelmet and int(class_id) in helmets:
                            # bounding_box = (x1, y1, x2, y2)
                            # bounding_box = tuple(map(lambda x: round(x, 2), bounding_box))
                            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
                            cv2.putText(annotated_frame, results_H_custom.names[int(class_id)].upper(),
                                        (int(x1), int(y1 - 10)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3, cv2.LINE_AA)

                # Draw the trapezoidal ROI on the frame
                cv2.polylines(annotated_frame, [np.array(roi_vertices, dtype=np.int32)], isClosed=True,
                              color=(255, 0, 0),
                              thickness=2)
                cv2.putText(annotated_frame, 'ROI: {}'.format(roi_vertices),
                            (roi_vertices[0][0], roi_vertices[0][1] - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 210), 2, cv2.LINE_AA)

                # Draw the prohibited ROI on the frame
                cv2.polylines(annotated_frame, [np.array(p_roi_vertices, dtype=np.int32)], isClosed=True,
                              color=(0, 0, 255),
                              thickness=2)
                cv2.putText(annotated_frame, 'Prohibited ROI: {}'.format(p_roi_vertices),
                            (p_roi_vertices[0][0], p_roi_vertices[0][1] - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)

                # Plot the tracks
                for box, track_id in zip(boxes, track_ids):
                    x, y, w, h = box
                    track = track_history[track_id]
                    track.append((float(x), float(y)))  # x, y center point
                    if len(track) > 30:  # retain 90 tracks for 90 frames
                        track.pop(0)

                    # Draw the tracking lines
                    points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                    cv2.polylines(annotated_frame, [points], isClosed=False, color=(230, 230, 230), thickness=5)

                # TODO: Only check for vehicles crossing if the prohibited ROI is defined
                # Check for vehicles crossing from roi_vertices to p_roi_vertices
                for prev_box, prev_id, box, track_id in zip(prev_boxes, prev_track_ids, boxes, track_ids):
                    prev_x, prev_y, prev_w, prev_h = prev_box
                    prev_center = (prev_x + prev_w / 2, prev_y + prev_h / 2)
                    x, y, w, h = box
                    center = (x + w / 2, y + h / 2)

                    # Check if the previous center was inside roi_vertices
                    prev_inside_roi = is_inside_trapezoid(prev_box, roi_vertices)

                    # Check if the current center is inside p_roi_vertices
                    current_inside_p_roi = is_inside_trapezoid(box, p_roi_vertices)

                    if prev_inside_roi and not current_inside_p_roi and prev_id not in crossed_vehicles:
                        # Vehicle transitioned from roi_vertices to p_roi_vertices and hasn't been processed yet
                        print(f"Vehicle with ID {prev_id} crossed from ROI to prohibited ROI.")
                        crossed_vehicles.add(prev_id)

                # Store current bounding boxes and track IDs for the next iteration
                prev_boxes = boxes
                prev_track_ids = track_ids

                # Display the annotated frame
                cv2.imshow("YOLOv8 Tracking", annotated_frame)

                out.write(annotated_frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # Break the loop if the end of the video is reached
            break

    # Release the video capture object and close the display window
    cap.release()
    cv2.destroyAllWindows()


def video_to_html(video_path, start_frame, end_frame):
    # Load the video
    cap = cv2.VideoCapture(video_path)

    # Check if the video is opened successfully
    if not cap.isOpened():
        raise ValueError("Error opening video file")

    # Get total number of frames in the video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Ensure end_frame does not exceed the total number of frames
    end_frame = min(end_frame, total_frames - 1)

    # Set the video to start from the start_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Start reading frames and yield them one by one
    current_frame = start_frame

    while current_frame <= end_frame:
        ret, frame = cap.read()

        if not ret:
            break  # Stop if there's an error reading the frame

        # Encode the frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Yield the frame as part of an HTTP response, simulating streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        # TODO: modify the sleep time to adjust the video playback speed
        # Mimic video playback speed (25 ms between frames)
        time.sleep(0.025)

        current_frame += 1

    cap.release()


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


