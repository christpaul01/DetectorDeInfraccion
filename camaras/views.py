from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from .models import Camara
from django.db.models import Max


def get_next_camera_id():
    """
    Returns the next available ID for a new camera.
    """
    if Camara.objects.exists():
        max_id = Camara.objects.aggregate(Max('id_camara'))['id_camara__max']
        return max_id + 1
    else:
        return 1

def home(request):
    camaras = Camara.objects.all()
    next_id = get_next_camera_id()
    context = {"camaras": camaras, "next_id": next_id}
    return render(request, "configCamaras.html", context)


def registarCamara(request):
    idCamara = get_next_camera_id()
    nombre = request.POST['nombreCamara']
    estado = request.POST['estadoCamara']
    resolucionCamara = request.POST['resolucionCamara']

    Camara.objects.create(id_camara=idCamara, nombre_camara=nombre, estado_camara=estado, resolucion_camara=resolucionCamara)
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
