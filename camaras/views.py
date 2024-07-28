from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from .models import Camara


def home(request):
    camaras = Camara.objects.all()
    return render(request, "configCamaras.html", {"camaras": camaras})



def registarCamara(request):
    idCamara = request.POST['idCamara']
    nombre = request.POST['nombreCamara']
    estado = request.POST['estadoCamara']
    resolucionCamara = request.POST['resolucionCamara']

    camara = Camara.objects.create(id_camara=idCamara, nombre_camara=nombre, estado_camara=estado, resolucion_camara=resolucionCamara)
    return redirect('/')

def editarCamara(request,id_camara):
    camara = Camara.objects.get(id_camara=id_camara)
    return render(request,'editarCamara.html', {"camara": camara})

#Error para completar la edicion, se supone que hay que enviar el id_camara pero en el tutorial no lo hacen de esa forma
def edicionCamara(request):
    idCamara = request.POST['idCamara']
    nombre = request.POST['nombreCamara']
    estado = request.POST['estadoCamara']
    resolucionCamara = request.POST['resolucionCamara']

    camara = Camara.objects.get(id_camara=idCamara)
    camara.id_camara = idCamara
    camara.nombre_camara = nombre
    camara.estado_camara = estado
    camara.resolucion_camara = resolucionCamara
    camara.save()
    return redirect('/')

def eliminarCamara(request,id_camara):
    camara = Camara.objects.get(id_camara=id_camara)
    camara.delete()
    return redirect('/')

def camaras(request):
    template = loader.get_template('configCamaras.html')
    return HttpResponse(template.render())
