from datetime import datetime
from threading import Thread

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, StreamingHttpResponse
from .forms import CustomUserCreationForm  # Import the custom form

from .models import Camara, Direccion, ROI, Infraccion
from .models import Umbral, TipoInfraccion, TipoVehiculo
from django.db.models import Max, DateField
from tkinter import filedialog
import cv2
from . import util as utilidades

# login imports

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.contrib import messages

from django.http import JsonResponse
from django.db.models import Count


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

# def home(request):
#     camaras = utilidades.get_camaras()
#     #camaras = Camara.objects.all()
#     next_id = get_next_camera_id()
#     direcciones = Direccion.objects.all()
#     context = {"camaras": camaras, "next_id": next_id, "direcciones": direcciones}
#     return render(request, "configCamaras.html", context)


def home(request):
    camaras = utilidades.get_camaras()
    next_id = get_next_camera_id()
    direcciones = Direccion.objects.all()

    # Verificar qué cámaras están activas
    camaras_estado = []
    for camara in camaras:
        esta_activa = camara.id_camara in utilidades.active_threads and utilidades.active_threads[camara.id_camara].is_alive()
        camaras_estado.append({
            "camara": camara,
            "esta_activa": esta_activa
        })

    context = {"camaras_estado": camaras_estado, "next_id": next_id, "direcciones": direcciones}
    return render(request, "configCamaras.html", context)

# Bloque Camaras
@login_required
def nuevaCamara(request):
    next_id = get_next_camera_id()
    direcciones = Direccion.objects.all()
    context = {"next_id": next_id, "direcciones": direcciones}
    return render(request, 'nuevaCamara.html', context)


@login_required
def registarCamara(request):
    if not permission_required('camaras.add_camara'):
        print("El usuario no tiene permisos")
        return redirect('/')


    idCamara = get_next_camera_id()
    nombre = request.POST['nombreCamara']
    estado = request.POST['estadoCamara']
    direccion = request.POST['idDireccionCamara']

    if direccion == "":
        direccion = None

    user = request.user

    isROINormalSelected = request.POST.get('ROINormal', True)
    isROIProhibidoSelected = request.POST.get('ROIProhibido', False)
    isLuzRojaSelected = request.POST.get('LuzRoja', False)
    maxROIProhibido = int(request.POST.get('maxROIProhibido', 1))

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
                              video_length=video_length, first_frame_base64=first_frame_64, user = user, id_direccion_camara_id=direccion)
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
        for i in range(maxROIProhibido):
            print(f"Seleccionando ROI Prohibido {i + 1}")
            coordenadas_p = utilidades.get_roi_vertices(
                utilidades.get_frame_from_video(url_video_path), f"Seleccione el ROI Prohibido {i + 1}")
            ROI.objects.create(
                id_camara=camaraInstance, coordenadas=coordenadas_p,
                estado_roi='A', tipo_roi='P', fecha_creacion=fechaCreacion
            )
    if isLuzRojaSelected:
        fechaCreacion = datetime.now()
        print("Luz Roja seleccionado")
        coordenadas_s = utilidades.get_roi_vertices(utilidades.get_frame_from_video(url_video_path), "Seleccione el ROI de la Luz Roja")
        ROI.objects.create(id_camara=camaraInstance, coordenadas=coordenadas_s, estado_roi='A', tipo_roi='S', fecha_creacion=fechaCreacion)

    return redirect('/')

@login_required
def stream_video(request, id_camara):
    # Attempt to get the camera object
    camara = get_object_or_404(Camara, id_camara=id_camara)

    # Prepare context for the template
    context = {
        'camara': camara,
        'video_url': f"/stream/{camara.id_camara}/video/"
    }

    return render(request, 'stream.html', context)

@login_required
def stream_infraccion(request, id_infraccion):
    # Attempt to get the infraccion object
    infraccion = get_object_or_404(Infraccion, id_infraccion=id_infraccion)

    # Prepare context for the template
    context = {
        'infraccion': infraccion,
        'video_url': f"/streamInfracciones/{infraccion.id_infraccion}/video/"
    }

    return render(request, 'streamInfraccion.html', context)

@login_required
def stream_infraccion_content(request, id_infraccion):
    try:
        infraccion = Infraccion.objects.get(id_infraccion=id_infraccion)
        camara = infraccion.id_camara
        video_path = camara.url_camara
    except Infraccion.DoesNotExist:
        error_type = "Error de procesamiento"
        error_message = "No se encontró la infracción solicitada."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

    start_frame = infraccion.frame_inicio
    end_frame = infraccion.frame_final

    # Call the modified function to stream frames
    response = StreamingHttpResponse(utilidades.video_to_html(video_path, start_frame, end_frame),
                                     content_type='multipart/x-mixed-replace; boundary=frame')

    return response


@login_required
def detallesInfraccion(request, id_infraccion):
    try:
        infraccion = Infraccion.objects.get(id_infraccion=id_infraccion)
        camara = infraccion.id_camara
        tipo_vehiculo = TipoVehiculo.objects.get(id_tipo_vehiculo=infraccion.id_tipo_vehiculo_id).nombre_tipo_vehiculo
        tipo_infraccion = TipoInfraccion.objects.get(id_tipo_infraccion=infraccion.tipo_infraccion_id).nombre_tipo_infraccion
        context = {"infraccion": infraccion, "camara": camara, "tipo_vehiculo": tipo_vehiculo, "tipo_infraccion": tipo_infraccion}
        return render(request, 'detallesInfraccion.html', context)
    except Infraccion.DoesNotExist:
        error_type = "Error de procesamiento"
        error_message = "No se encontró la infracción solicitada."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)


@login_required
def confirmarInfraccion(request, id_infraccion):
    nombreUsuario = request.user.username
    infraccion = Infraccion.objects.get(id_infraccion=id_infraccion)
    infraccion.estado_infraccion = 'Confirmada'
    infraccion.revision_infraccion = f'Confirmada por usuario: {nombreUsuario}'
    infraccion.save()
    return redirect(listarInfracciones)

@login_required
def denegarInfraccion(request, id_infraccion):
    nombreUsuario = request.user.username
    infraccion = Infraccion.objects.get(id_infraccion=id_infraccion)
    infraccion.estado_infraccion = 'Denegada'
    infraccion.revision_infraccion = f'Denegada por usuario: {nombreUsuario}'
    infraccion.save()
    return redirect(listarInfracciones)

@login_required
def eliminarInfraccion(request, id_infraccion):
    isAdmin = request.user.groups.filter(name='Admin').exists()
    if not isAdmin:
        error_type = "Error de permisos"
        error_message = "No tienes permisos para borrar infracciones."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

    infraccion = Infraccion.objects.get(id_infraccion=id_infraccion)
    infraccion.delete()
    return redirect(listarInfracciones)

@login_required
def stream_video_content(request, id_camara):
    try:
        camara = Camara.objects.get(id_camara=id_camara)
        video_path = camara.url_camara
    except Camara.DoesNotExist:
        return StreamingHttpResponse("Video not found", status=404)

    # TODO: Get the start and end frame from the request if needed
    start_frame = 0
    end_frame = 500

    # Call the modified function to stream frames
    response = StreamingHttpResponse(utilidades.video_to_html(video_path, start_frame, end_frame),
                                     content_type='multipart/x-mixed-replace; boundary=frame')
    return response

@login_required
def start_camara(request, id_camara):
    camara = Camara.objects.get(id_camara=id_camara)

    # Start vehicle detection via a Thread
    #Thread(target=utilidades.start_vehicle_detection, args=(camara.id_camara,)).start()
    utilidades.iniciar_hilo_camara(camara.id_camara)
    return redirect('/')

@login_required
def stop_camara(request, id_camara):
    camara = Camara.objects.get(id_camara=id_camara)
    utilidades.detener_hilo_camara(camara.id_camara)
    return redirect('/')


def check_thread_status(request, id_camara):
    # Assuming you have a function that can check if the thread is still running
    thread_status = utilidades.is_thread_running(id_camara)

    #print(f"Thread status for camera {id_camara}: {thread_status}")

    return JsonResponse({
        'is_active': thread_status
    })

@login_required
def editarCamara(request,id_camara):
    try:
        camara = Camara.objects.get(id_camara=id_camara)
        direccionCamara = camara.id_direccion_camara_id
        dirreciones = Direccion.objects.all()
        has_roi_n = ROI.objects.filter(id_camara=id_camara, tipo_roi='N').exists()
        cant_roi_p = ROI.objects.filter(id_camara=id_camara, tipo_roi='P').count()
        has_roi_p = cant_roi_p > 0
        has_luz_roja = ROI.objects.filter(id_camara=id_camara, tipo_roi='S').exists()


        context = {"camara": camara, "has_roi_n": has_roi_n, "has_luz_roja": has_luz_roja,
                   "has_roi_p": has_roi_p, "cant_roi_p": cant_roi_p, "direcciones": dirreciones,
                   "direccionCamara": direccionCamara}

        return render(request, 'editarCamara.html', context)
    except Camara.DoesNotExist:
        error_type = "Error de procesamiento"
        error_message = "No se encontró la cámara solicitada."
        context = {"error_type": error_type, "error_message": error_message}

        return render(request, 'error.html', context)


def detallesCamara(request, id_camara):
    try:
        camara = Camara.objects.get(id_camara=id_camara)
        direccion_camara = Direccion.objects.filter(id_direccion=camara.id_direccion_camara_id).first()
        if direccion_camara is not None:
            direccion_camara = direccion_camara.nombre_direccion
        else:
            direccion_camara = None

        cant_roi_p = ROI.objects.filter(id_camara=id_camara, tipo_roi='P').count()
        has_roi_p = cant_roi_p > 0
        has_luz_roja = ROI.objects.filter(id_camara=id_camara, tipo_roi='S').first() is not None

        context = {"camara": camara, "has_roi_p": has_roi_p, "has_luz_roja":has_luz_roja, "cant_roi_p": cant_roi_p, "direccion": direccion_camara}
        return render(request, 'detallesCamara.html', context)
    except Camara.DoesNotExist:
        error_type = "Error de procesamiento"
        error_message = "No se encontró la cámara solicitada."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

# TODO: Mejorar funcion con recepcion de ID en el request
@login_required
def edicionCamara(request):

    if not request.user.has_perm('camaras.change_camara'):
        error_type = "Error de permisos"
        error_message = "No tienes permisos para editar cámaras."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

    if request.method == 'POST':
        idCamara = request.POST['idCamara']
        nombre = request.POST['nombreCamara']
        estado = request.POST['estadoCamara']
        direccionCamara = request.POST['idDireccionCamara']
        threshold_vehicle = request.POST['thresholdVehicle']
        threshold_license_plate = request.POST['thresholdLicensePlate']
        threshold_helmet = request.POST['thresholdHelmet']
        maxROIProhibido = int(request.POST.get('maxROIProhibido', 1))



        isROIProhibidoSelected = request.POST.get('ROIProhibido', False)
        isLuzRojaSelected = request.POST.get('LuzRoja', False)
        is_roi_edit = request.POST.get('editarROI') == 'Si'
        video_path = Camara.objects.get(id_camara=idCamara).url_camara

        try :
            camara = Camara.objects.get(id_camara=idCamara)
            camara.id_camara = idCamara
            camara.nombre_camara = nombre
            camara.estado_camara = estado
            camara.id_direccion_camara_id = direccionCamara
            camara.threshold_vehicle = threshold_vehicle
            camara.threshold_license_plate = threshold_license_plate
            camara.threshold_helmet = threshold_helmet
            camara.save()

            # Check if the camera has a normal ROI
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

            # Check if the camera has a prohibited ROI
            try:
                list_id_roi_p = ROI.objects.filter(id_camara=idCamara, tipo_roi='P').values_list('id_roi', flat=True)
            except ROI.DoesNotExist:
                list_id_roi_p = None

            if list_id_roi_p:
                if is_roi_edit:
                    if isROIProhibidoSelected:
                        # Get all the ID of the ROI Prohibido
                        list_id_roi_p = ROI.objects.filter(id_camara=idCamara, tipo_roi='P').values_list('id_roi', flat=True)
                        # Modify all the existing ROIs Prohibidos
                        if maxROIProhibido == len(list_id_roi_p):
                            for id_roi_p in list_id_roi_p:
                                roi_p = ROI.objects.get(id_roi=id_roi_p)
                                coordenadas_p = utilidades.get_roi_vertices(utilidades.get_frame_from_video(video_path), "Seleccione el ROI Prohibido")
                                roi_p.coordenadas = coordenadas_p
                                roi_p.fecha_creacion = datetime.now()
                                roi_p.save()
                        else:
                            for id_roi_p in list_id_roi_p:
                                roi_p = ROI.objects.get(id_roi=id_roi_p)
                                roi_p.delete()
                            for i in range(maxROIProhibido):
                                coordenadas_p = utilidades.get_roi_vertices(utilidades.get_frame_from_video(video_path), f"Seleccione el ROI Prohibido # {i}")
                                fecha_creacion = DateField(auto_now_add=True)
                                ROI.objects.create(id_camara=camara, coordenadas=coordenadas_p, estado_roi='A', tipo_roi='P', fecha_creacion=fecha_creacion)
                else:
                    if not isROIProhibidoSelected:
                        # TODO: Modificar el estado del ROI a inactivo
                        # Delete all the existing ROIs Prohibidos
                        for id_roi_p in list_id_roi_p:
                            roi_p = ROI.objects.get(id_roi=id_roi_p)
                            roi_p.delete()
            else:
                if isROIProhibidoSelected:
                    for i in range(maxROIProhibido):
                        coordenadas_p = utilidades.get_roi_vertices(utilidades.get_frame_from_video(video_path), f"Seleccione el ROI Prohibido # {i}")
                        fecha_creacion = DateField(auto_now_add=True)
                        ROI.objects.create(id_camara=camara, coordenadas=coordenadas_p, estado_roi='A', tipo_roi='P', fecha_creacion=fecha_creacion)
            # Check if the camera has a traffic light ROI
            try:
                roi_luz_roja = ROI.objects.get(id_camara=idCamara, tipo_roi='S')
            except ROI.DoesNotExist:
                roi_luz_roja = None

            if roi_luz_roja:
                if is_roi_edit:
                    if isLuzRojaSelected:
                        coordenadas_s = utilidades.get_roi_vertices(utilidades.get_frame_from_video(video_path), "Seleccione el ROI de la Luz Roja")
                        roi_luz_roja.coordenadas = coordenadas_s
                        roi_luz_roja.fecha_creacion = datetime.now()
                        roi_luz_roja.save()
                else:
                    if not isLuzRojaSelected:
                        roi_luz_roja.delete()
            else:
                if isLuzRojaSelected:
                    coordenadas_s = utilidades.get_roi_vertices(utilidades.get_frame_from_video(video_path), "Seleccione el ROI de la Luz Roja")
                    fecha_creacion = DateField(auto_now_add=True)
                    ROI.objects.create(id_camara=camara, coordenadas=coordenadas_s, estado_roi='A', tipo_roi='S', fecha_creacion=fecha_creacion)
            return redirect('/')
        except Camara.DoesNotExist:
            error_type = "Error de procesamiento"
            error_message = "No existe la cámara de ID:" + idCamara
            context = {"error_type": error_type, "error_message": error_message}
            return render(request, 'error.html', context)

# TODO: Cambiar a estado inactivo
@login_required
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


@login_required
def verConfiguracionSistema(request):

    umbrales = Umbral.objects.all()
    tipoInfracciones = TipoInfraccion.objects.all()
    tipoVehiculos = TipoVehiculo.objects.all()

    context = {"umbrales": umbrales, "tipoInfracciones": tipoInfracciones, "tipoVehiculos": tipoVehiculos}
    return render(request, 'verConfiguracionSistema.html', context)






# NOTE: Bloque Direccion

def listarDirecciones(request):
    direcciones = Direccion.objects.all()
    context = {"direcciones": direcciones}
    return render(request, 'listarDirecciones.html', context)


def verDireccion(request, id_direccion):
    direccion = Direccion.objects.get(id_direccion=id_direccion)
    context = {"direccion": direccion}
    return render(request, 'verDireccion.html', context)


def gestionDirecciones(request):
    direcciones = Direccion.objects.all()
    next_id = get_next_direccion_id()
    context = {"next_id": next_id, "direcciones": direcciones}
    return render(request, 'configDireccion.html', context)

@login_required
def editarDireccion(request, id_direccion):
    if not request.user.has_perm('camaras.change_direccion'):
        error_type = "Error de permisos"
        error_message = "No tienes permisos para editar direcciones."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)
    else:
        print("El usuario tiene permisos")

    if(request.method == 'GET'):
        direccion = Direccion.objects.get(id_direccion=id_direccion)
        context = {"direccion": direccion}
        return render(request, 'editarDireccion.html', context)

    if(request.method == 'POST'):
        nombre_direccion = request.POST['nombreDireccion']
        municipio = request.POST['municipio']
        ciudad = request.POST['ciudad']
        pais = request.POST['pais']
        detalles = request.POST['detalles']
        google_maps_url = request.POST['googleMapsUrl']
        google_embeded_url = request.POST['googleMapsEmbeddedUrl']
        valid_google_iframe = utilidades.validate_google_maps_iframe(google_embeded_url)

        if not valid_google_iframe:
            error_type = "Error de procesamiento"
            error_message = "El URL de Google Maps Embeded no es válido."
            context = {"error_type": error_type, "error_message": error_message}
            return render(request, 'error.html', context)

        (Direccion.objects.filter(id_direccion=id_direccion).update
         (nombre_direccion=nombre_direccion, municipio=municipio, ciudad=ciudad,
          pais=pais, detalles=detalles, google_maps_url=google_maps_url,
          google_embeded_url=google_embeded_url))
        return redirect('/direcciones/')

@login_required
def eliminarDireccion(request, id_direccion):
    has_permission = request.user.has_perm('camaras.delete_direccion')
    if not has_permission:
        error_type = "Error de permisos"
        error_message = "No tienes permisos para eliminar direcciones."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)


    try:
        direccion = Direccion.objects.get(id_direccion=id_direccion)
        direccion.delete()
    except Direccion.DoesNotExist:
        error_type = "Error de procesamiento"
        error_message = "No se encontró la dirección solicitada."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)
    return redirect('/direcciones/')

@login_required
def registrarDireccion(request):
    idDireccion = request.POST['idDireccion']
    nombreDireccion = request.POST['nombreDireccion']
    municipio = request.POST['municipio']
    ciudad = request.POST['ciudad']
    pais = request.POST['pais']
    detalles = request.POST['detalles']
    google_maps_url = request.POST['googleMapsUrl']
    google_embeded_url = request.POST['googleMapsEmbeddedUrl']

    valid_google_iframe = utilidades.validate_google_maps_iframe(google_embeded_url)

    if not valid_google_iframe:
        error_type = "Error de procesamiento"
        error_message = "El URL de Google Maps Embeded no es válido."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

    Direccion.objects.create(id_direccion=idDireccion, nombre_direccion=nombreDireccion,
                             municipio=municipio, ciudad=ciudad, pais=pais, detalles=detalles,
                             google_maps_url=google_maps_url, google_embeded_url=google_embeded_url)
    return redirect('/direcciones/')



# NOTES: Login, Logout and Register views
def loginpage(request):

    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'GET':
        return render(request, 'login.html')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            # Convierte al usuario en Admin si es superusuario y no es Admin
            if user.is_superuser and not user.groups.filter(name='Admin').exists():
                admin_group = Group.objects.get(name='Admin')
                user.groups.add(admin_group)

            messages.success(request, f'You are logged in as {user.username}')
            return redirect('/')
        else:
            messages.error(request, 'The combination of the user name and the password is wrong!')
            return redirect('login')


@login_required
def registerpage(request):

    # check if user is not admin
    if not request.user.groups.filter(name='Admin').exists():
        error_type = "Error de permisos"
        error_message = "No tienes permisos para registrar usuarios."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

    if request.method == 'GET':
        return render(request, 'register.html')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            email = form.cleaned_data.get('email')
            role = request.POST['role']
            user = form.save()

            # Authenticate user after saving
            user = authenticate(username=username, password=password)

            # Asignar grupo según el rol seleccionado
            if role == 'Admin':
                admin_group = Group.objects.get(name='Admin')
                user.groups.add(admin_group)
            elif role == 'NormalStaff':
                normal_group = Group.objects.get(name='NormalStaff')
                user.groups.add(normal_group)

            messages.success(request, f'You have registered {user.username} account successfully!')
            return redirect('/')
        else:
            messages.error(request, form.errors)
            return redirect('register')

def logoutpage(request):
    logout(request)
    messages.success(request, f'You have been logged out!')
    return redirect('/')


# NOTE: Bloque Usuarios y Grupos

def set_user_to_admin(request, id):
    if request.method == 'POST' or request.method == 'GET':
        if not request.user.has_perm('camaras.change_user'):
            error_type = "Error de permisos"
            error_message = "No tienes permisos para cambiar el rol de los usuarios."
            context = {"error_type": error_type, "error_message": error_message}
            return render(request, 'error.html', context)
        else:
            user = User.objects.get(id=id)
            admin_group = Group.objects.get(name='Admin')
            user.groups.add(admin_group)
            return redirect('/listarUsuarios')

def change_user_to_normal_staff(request, id):
    if request.method == 'POST' or request.method == 'GET':
        if not request.user.has_perm('camaras.change_user'):
            error_type = "Error de permisos"
            error_message = "No tienes permisos para cambiar el rol de los usuarios."
            context = {"error_type": error_type, "error_message": error_message}
            return render(request, 'error.html', context)
        else:
            user = User.objects.get(id=id)
            if user:
                if user.is_superuser:
                    messages.error(request, 'No se puede cambiar el rol de un superusuario.')
                    return redirect('/listarUsuarios')
                # Remove the user from the Admin group
                admin_group = Group.objects.get(name='Admin')
                user.groups.remove(admin_group)
                # Add the user to the NormalStaff group
                normal_staff_group = Group.objects.get(name='NormalStaff')
                user.groups.add(normal_staff_group)
            else:
                error_type = "Error de procesamiento"
                error_message = "No se encontró el usuario solicitado."
                context = {"error_type": error_type, "error_message": error_message}
                return render(request, 'error.html', context)

            return redirect('/listarUsuarios')

@login_required
def listar_usuarios(request):
    if not request.user.groups.filter(name='Admin').exists():
        error_type = "Error de permisos"
        error_message = "No tienes permisos para ver la lista de usuarios."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)


    usuarios = User.objects.all()
    usuarios_info = []

    for user in usuarios:
        is_admin = user.groups.filter(name="Admin").exists()
        is_normal_staff = user.groups.filter(name="NormalStaff").exists()
        print(f"User: {user.username}, is_admin: {is_admin}, is_normal_staff: {is_normal_staff}")
        usuarios_info.append({
            "user": user,
            "is_admin": is_admin,
            "is_normal_staff": is_normal_staff,
        })

    context = {"usuarios_info": usuarios_info}
    return render(request, 'listarUsuarios.html', context)

def cambiarEstadoCuenta(request, id):
    if request.method == 'POST' or request.method == 'GET':
        if not request.user.has_perm('camaras.change_user'):
            error_type = "Error de permisos"
            error_message = "No tienes permisos para cambiar el rol de los usuarios."
            context = {"error_type": error_type, "error_message": error_message}
            return render(request, 'error.html', context)
        else:
            user = User.objects.get(id=id)
            if user:
                if user.is_superuser:
                    if not user.is_active:
                        user.is_active = not user.is_active
                        user.save()
                        return redirect('/listarUsuarios')
                    else:
                        messages.error(request, 'No se puede desactivar la cuenta de un superusuario.')
                        return redirect('/listarUsuarios')

                user.is_active = not user.is_active
                user.save()
                return redirect('/listarUsuarios')
            else:
                error_type = "Error de procesamiento"
                error_message = "No se encontró el usuario solicitado."
                context = {"error_type": error_type, "error_message": error_message}
                return render(request, 'error.html', context)


# NOTE: Bloque Infracciones

def listarInfracciones(request):
    if not request.user.groups.filter(name='Admin').exists():
        error_type = "Error de permisos"
        error_message = "No tienes permisos para ver la lista de infracciones."
        context = {"error_type": error_type, "error_message": error_message}
        return render(request, 'error.html', context)

    infracciones = Infraccion.objects.all()
    # sort infracciones by estado infracciones pendiente then confirmada then denegada and by date
    infracciones = sorted(infracciones, key=lambda x: (x.estado_infraccion, x.fecha_infraccion), reverse=True)
    context = {"infracciones": infracciones}

    return render(request, 'listarInfracciones.html', context)

# NOTE: Ajustes del Sistema

def estadisticas(request):
    # 1. Obtener datos dinámicos
    top_direcciones = (
        Direccion.objects.annotate(infracciones_totales=Count('camara__infraccion'))
        .order_by('-infracciones_totales')[:5]
    )
    tipos_infracciones = (
        TipoInfraccion.objects.annotate(infracciones_totales=Count('infraccion'))
        .order_by('-infracciones_totales')
    )
    tipo_vehiculos = (
        TipoVehiculo.objects.annotate(infracciones_totales=Count('infraccion'))
        .order_by('-infracciones_totales')
    )
    estado_infracciones = (
        Infraccion.objects.values('estado_infraccion').annotate(total=Count('id_infraccion'))
    )
    camara_top = (
        Camara.objects.annotate(infracciones_totales=Count('infraccion'))
        .order_by('-infracciones_totales')[:1]
    )

    # 2. Preparar datos para renderizar en JSON/JavaScript
    context = {
        "top_direcciones": [{"nombre": d.nombre_direccion, "total": d.infracciones_totales} for d in top_direcciones],
        "tipos_infracciones": [{"nombre": t.nombre_tipo_infraccion, "total": t.infracciones_totales} for t in tipos_infracciones],
        "tipo_vehiculos": [{"nombre": v.nombre_tipo_vehiculo, "total": v.infracciones_totales} for v in tipo_vehiculos],
        "estado_infracciones": list(estado_infracciones),
        "camara_top": [{"nombre": c.nombre_camara, "total": c.infracciones_totales} for c in camara_top],
    }

    # 3. Renderizar plantilla con datos
    return render(request, 'dashboards.html', context)

@login_required
def ajustesSistema(request):
    return render(request, 'ajustesSistema.html')