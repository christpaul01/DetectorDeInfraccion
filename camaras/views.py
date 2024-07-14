from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader

def camaras(request):
    if request.method == 'POST':
        # Handle form submission
        camera_name = request.POST.get('camera_name')
        camera_location = request.POST.get('camera_location')
        print(camera_name, camera_location)
        return redirect('camaras')
    else:
        context = {
            'camera_name': 'Camera 1',
            'camera_location': 'Main Street'
        }
        return render(request, 'configCamaras.html', context)