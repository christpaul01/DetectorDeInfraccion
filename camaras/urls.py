from django.urls import path
from . import views

urlpatterns = [
    # Bloque Home
    path('', views.home),
    # Bloque Camaras
    path('camaras/', views.camaras, name='camaras'),
    path('iniciarCamara/<id_camara>', views.start_camara),
    path('nuevaCamara/', views.nuevaCamara),
    path('registrarCamara/', views.registarCamara),
    path('editarCamara/<id_camara>', views.editarCamara),
    path('detallesCamara/<id_camara>', views.detallesCamara),
    path('edicionCamara/', views.edicionCamara),
    path('eliminarCamara/<id_camara>', views.eliminarCamara),

    # Bloque Direcciones
    path('direcciones/', views.gestionDirecciones),

    path('direcciones/eliminarDireccion/<id_direccion>', views.eliminarDireccion),

    path('listarDirecciones/', views.listarDirecciones),

    path('registrarDireccion/', views.registrarDireccion)
]
