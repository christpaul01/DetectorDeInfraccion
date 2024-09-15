from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('camaras/', views.camaras, name='camaras'),
    path('registrarCamara/', views.registarCamara),
    path('editarCamara/<id_camara>', views.editarCamara),
    path('edicionCamara/', views.edicionCamara),
    path('eliminarCamara/<id_camara>', views.eliminarCamara),
    path('video', views.index)
]
