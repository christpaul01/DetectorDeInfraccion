from django.urls import path
from . import views

urlpatterns = [
    # Bloque Home
    path('', views.home, name='home'),
    # Bloque Camaras
    # path('camaras/', views.camaras, name='camaras'),
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

    path('registrarDireccion/', views.registrarDireccion),

    path('direcciones/editarDireccion/<int:id_direccion>', views.editarDireccion),
    # Visualizacion de direccion
    path('direcciones/verDireccion/<int:id_direccion>', views.verDireccion, name='direccion'),



   # path('stream/<id_camara>', views.stream_video, name='stream_video')
    path('stream/<int:id_camara>/', views.stream_video, name='stream_video'),
    path('stream/<int:id_camara>/video/', views.stream_video_content, name='stream_video_content'),

    # login path
    path('login/', views.loginpage, name='login'),

    # logout path
    path('logout/', views.logoutpage, name='logout'),

    # register path
    path('register/', views.registerpage, name='register'),

    # set User to Admnin
    path('setAdmin/<int:id>', views.set_user_to_admin, name='setAdmin'),

    # NOTE: This path is for settings
    path('configuracion/', views.verConfiguracionSistema, name='configuracionSistema'),


]
