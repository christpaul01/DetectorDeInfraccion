from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def camaras(request):
  template = loader.get_template('configCamaras.html')
  return HttpResponse(template.render())