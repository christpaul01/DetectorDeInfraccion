from datetime import datetime

from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse
from django.template import loader


from .models import Camara, Direccion, ROI
from django.db.models import Max, DateField
from tkinter import filedialog
import cv2
from . import util as utilidades


def get_next_camera_id():
    """
    Returns the next available ID for a new camera.
    """
    if Camara.objects.exists():
        max_id = Camara.objects.aggregate(Max('id_camara'))['id_camara__max']
        return max_id + 1
    else:
        return 1

def get_next_direccion_id():
    """
    Returns the next available ID for a new direccion.
    """
    if Direccion.objects.exists():
        max_id = Direccion.objects.aggregate(Max('id_direccion'))['id_direccion__max']
        return max_id + 1
    else:
        return 1

def home(request):
    camaras = utilidades.get_camaras()
    #camaras = Camara.objects.all()
    next_id = get_next_camera_id()
    context = {"camaras": camaras, "next_id": next_id}
    return render(request, "configCamaras.html", context)


# Bloque Camaras

def nuevaCamara(request):
    next_id = get_next_camera_id()
    context = {"next_id": next_id}
    return render(request, 'nuevaCamara.html', context)

def registarCamara(request):
    idCamara = get_next_camera_id()
    nombre = request.POST['nombreCamara']
    estado = request.POST['estadoCamara']

    isROINormalSelected = request.POST.get('ROINormal', True)
    isROIProhibidoSelected = request.POST.get('ROIProhibido', False)

    #resolucionCamara = request.POST['resolucionCamara']

    url_video_path = filedialog.askopenfilename()

    video_info = None

    try:
        # obtaining video information
        # TODO: Validate if the file is a valid video file
        video_info = utilidades.get_video_info(url_video_path)

        width = video_info[0]
        height = video_info[1]
        fps = video_info[2]
        frame_count_video = video_info[3]
        video_length = video_info[4]
        first_frame = video_info[5]

        # put resolution in a string
        resolucionCamara = str(width) + "x" + str(height)

    except cv2.error as e:
        error_type = "Error de procesamiento"
        error_message = "No se pudo obtener las informaciones del video."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

    if video_info is not None:
        first_frame_64 = utilidades.frame_to_base64(first_frame)
        Camara.objects.create(id_camara=idCamara, nombre_camara=nombre, url_camara= url_video_path,
                              estado_camara=estado, frame_rate=fps, resolucion_camara=resolucionCamara,
                              fecha_creacion = datetime.now(),frame_count=frame_count_video,
                              video_length=video_length, first_frame_base64=first_frame_64)
    else:
        error_type = "Error de procesamiento"
        error_message = "No se pudo obtener las informaciones del video."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

    # get created Camara id

    camaraInstance = Camara.objects.get(id_camara=idCamara)

    if isROINormalSelected:
        fechaCreacion = datetime.now()
        print("ROI Normal seleccionado")
        coordenadas_n = utilidades.get_roi_vertices(utilidades.get_frame_from_video(url_video_path), "Seleccione el ROI Normal")
        print ("Coordenadas Normal`: ", coordenadas_n)

        ROI.objects.create(id_camara=camaraInstance, coordenadas=coordenadas_n, estado_roi='A', tipo_roi='N', fecha_creacion=fechaCreacion)

    if isROIProhibidoSelected:
        fechaCreacion = datetime.now()
        print("ROI Prohibido seleccionado")
        coordenadas_p = utilidades.get_roi_vertices(utilidades.get_frame_from_video(url_video_path), "Seleccione el ROI Prohibido")
        ROI.objects.create(id_camara=camaraInstance, coordenadas= coordenadas_p, estado_roi='A', tipo_roi='P', fecha_creacion=fechaCreacion)


    return redirect('/')


def stream_video(request, id_camara):
    # NOTE: For testing purposes, the original video is streamed
    # TODO: Modify this function to stream infraccion videos instead of the original video
    try:
        camara = Camara.objects.get(id_camara=id_camara)
        video_path = camara.url_camara
    except Camara.DoesNotExist:
        print("No se encontró la cámara solicitada.")
        error_type = "Error de procesamiento"
        error_message = "No se encontró la cámara solicitada."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

    # TODO: Get the start and end frame from the request
    start_frame = 0
    end_frame = 100

    # Call the modified function to stream frames
    response = StreamingHttpResponse(utilidades.video_to_html(video_path, start_frame, end_frame),
                                     content_type='multipart/x-mixed-replace; boundary=frame')
    return response

def start_camara(request, id_camara):
    camara = Camara.objects.get(id_camara=id_camara)
    utilidades.start_detection(camara.id_camara)
    return redirect('/')

def editarCamara(request,id_camara):
    try:
        camara = Camara.objects.get(id_camara=id_camara)
        has_roi_n = ROI.objects.filter(id_camara=id_camara, tipo_roi='N').exists()
        has_roi_p = ROI.objects.filter(id_camara=id_camara, tipo_roi='P').exists()
        context = {"camara": camara, "has_roi_n": has_roi_n, "has_roi_p": has_roi_p}

        return render(request, 'editarCamara.html', context)
    except Camara.DoesNotExist:
        error_type = "Error de procesamiento"
        error_message = "No se encontró la cámara solicitada."
        context = {"error_type": error_type, "error_message": error_message}

        return render(request, 'error.html', context)


def detallesCamara(request, id_camara):
    try:
        camara = Camara.objects.get(id_camara=id_camara)
        has_roi_p = ROI.objects.filter(id_camara=id_camara, tipo_roi='P').first() is not None

        context = {"camara": camara, "has_roi_p": has_roi_p}
        return render(request, 'detallesCamara.html', context)
    except Camara.DoesNotExist:
        error_type = "Error de procesamiento"
        error_message = "No se encontró la cámara solicitada."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

#Error para completar la edicion, se supone que hay que enviar el id_camara pero en el tutorial no lo hacen de esa forma
def edicionCamara(request):
    idCamara = request.POST['idCamara']
    nombre = request.POST['nombreCamara']
    estado = request.POST['estadoCamara']

    isROIProhibidoSelected = request.POST.get('ROIProhibido', False)
    is_roi_edit = request.POST.get('editarROI') == 'Si'
    video_path = Camara.objects.get(id_camara=idCamara).url_camara

    try :
        camara = Camara.objects.get(id_camara=idCamara)
        camara.id_camara = idCamara
        camara.nombre_camara = nombre
        camara.estado_camara = estado
        camara.save()

        try:
            roi_n = ROI.objects.get(id_camara=idCamara, tipo_roi='N')
        except ROI.DoesNotExist:
            roi_n = None

        if roi_n:
            if is_roi_edit:
                coordenadas_n = utilidades.get_roi_vertices(utilidades.get_frame_from_video(video_path), "Seleccione el ROI Normal")
                roi_n.coordenadas = coordenadas_n
                roi_n.fecha_creacion = datetime.now()
                roi_n.save()
        else:
            coordenadas_n = utilidades.get_roi_vertices(utilidades.get_frame_from_video(video_path), "Seleccione el ROI Normal")
            fecha_creacion = DateField(auto_now_add=True)
            ROI.objects.create(id_camara=camara, coordenadas=coordenadas_n, estado_roi='A', tipo_roi='N', fecha_creacion=fecha_creacion)


        try:
            roi_p = ROI.objects.get(id_camara=idCamara, tipo_roi='P')
        except ROI.DoesNotExist:
            roi_p = None

        if roi_p:
            if is_roi_edit:
                if isROIProhibidoSelected:
                    coordenadas_p = utilidades.get_roi_vertices(utilidades.get_frame_from_video(video_path), "Seleccione el ROI Prohibido")
                    roi_p.coordenadas = coordenadas_p
                    roi_p.fecha_creacion = datetime.now()
                    roi_p.save()
            else:
                if not isROIProhibidoSelected:
                    # TODO: Modificar el estado del ROI a inactivo
                    roi_p.delete()
        else:
            if isROIProhibidoSelected:
                coordenadas_p = utilidades.get_roi_vertices(utilidades.get_frame_from_video(video_path), "Seleccione el ROI Prohibido")
                fecha_creacion = DateField(auto_now_add=True)
                ROI.objects.create(id_camara=camara, coordenadas=coordenadas_p, estado_roi='A', tipo_roi='P', fecha_creacion=fecha_creacion)

        return redirect('/')
    except Camara.DoesNotExist:
        error_type = "Error de procesamiento"
        error_message = "No existe la cámara de ID:" + idCamara
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)


def eliminarCamara(request,id_camara):
    try:
        camara = Camara.objects.get(id_camara=id_camara)
        camara.delete()
    except Camara.DoesNotExist:
        error_type = "Error de procesamiento"
        error_message = "No existe la cámara solicitada."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)
    return redirect('/')

def camaras(request):

    template = loader.get_template('configCamaras.html')
    return HttpResponse(template.render())

# NOTE: Bloque Direccion


def listarDirecciones(request):
    direcciones = Direccion.objects.all()
    context = {"direcciones": direcciones}
    return render(request, 'listarDirecciones.html', context)

def gestionDirecciones(request):
    direcciones = Direccion.objects.all()
    next_id = get_next_direccion_id()
    context = {"next_id": next_id, "direcciones": direcciones}
    return render(request, 'configDireccion.html', context)

def eliminarDireccion(request, id_direccion):
    try:
        direccion = Direccion.objects.get(id_direccion=id_direccion)
        direccion.delete()
    except Direccion.DoesNotExist:
        error_type = "Error de procesamiento"
        error_message = "No se encontró la dirección solicitada."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)
    return redirect('/direcciones/')

def registrarDireccion(request):
    idDireccion = request.POST['idDireccion']
    nombreDireccion = request.POST['nombreDireccion']
    municipio = request.POST['municipio']
    ciudad = request.POST['ciudad']
    pais = request.POST['pais']
    detalles = request.POST['detalles']

    Direccion.objects.create(id_direccion=idDireccion, nombre_direccion=nombreDireccion, municipio=municipio, ciudad=ciudad, pais=pais, detalles=detalles)
    return redirect('/direcciones/')