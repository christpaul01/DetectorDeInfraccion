from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from .models import Camara, Direccion
from django.db.models import Max
from tkinter import filedialog


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
    camaras = Camara.objects.all()
    next_id = get_next_camera_id()
    context = {"camaras": camaras, "next_id": next_id}
    return render(request, "configCamaras.html", context)


# Bloque Camaras

def registarCamara(request):
    idCamara = get_next_camera_id()
    nombre = request.POST['nombreCamara']
    estado = request.POST['estadoCamara']
    resolucionCamara = request.POST['resolucionCamara']

    url_video_path = filedialog.askopenfilename()



    Camara.objects.create(id_camara=idCamara, nombre_camara=nombre, url_camara= url_video_path, estado_camara=estado, resolucion_camara=resolucionCamara)
    return redirect('/')

def editarCamara(request,id_camara):
    try:
        camara = Camara.objects.get(id_camara=id_camara)
        return render(request, 'editarCamara.html', {"camara": camara})
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
    resolucionCamara = request.POST['resolucionCamara']

    try :
        camara = Camara.objects.get(id_camara=idCamara)
        camara.id_camara = idCamara
        camara.nombre_camara = nombre
        camara.estado_camara = estado
        camara.resolucion_camara = resolucionCamara
        camara.save()
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