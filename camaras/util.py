import cv2

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

    # Liberar el recurso del video
    cap.release()

    # Retornar la información
    return frame_width, frame_height, fps
