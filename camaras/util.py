import cv2

import numpy as np
import datetime
import os
import tkinter as tk
from tkinter import filedialog

def get_time_from_seconds(seconds):
    """
    Convierte una cantidad de segundos a una cadena de texto en formato HH:MM:SS.

    Args:
        seconds (int): La cantidad de segundos.

    Returns:
        str: Una cadena de texto en formato HH:MM:SS.
    """
    return str(datetime.timedelta(seconds=seconds))


def get_video_info(video_path):
    """
    Obtiene la resolución (ancho y alto) y los FPS de un archivo de video.

    Args:
        video_path (str): La ruta del archivo de video.

    Returns:
        tuple: Una tupla que contiene (ancho, alto, fps) o None si no se puede abrir el video.
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

    # Liberar el recurso del video
    cap.release()

    # Retornar la información
    return frame_width, frame_height, fps, frame_count, video_length


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


