from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def camaras(request):
    context = {
        'camera_name': 'Camera 1',
        'camera_location': 'Main Street'
    }
    return render(request, 'configCamaras.html', context)