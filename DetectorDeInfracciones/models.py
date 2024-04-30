import  django
from django.db import models
import os



class User(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    id_rol_usuario = models.ForeignKey('RolUsuario', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField()
    estado_usuario = models.CharField(max_length=255)
    direccion_usuario = models.CharField(max_length=255)
    correo = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class ROI(models.Model):
    id_roi = models.AutoField(primary_key=True)
    id_direccion = models.ForeignKey('Direccion', on_delete=models.CASCADE)
    estado_roi = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField()
    tipo_roi = models.CharField(max_length=255)
    coordenadas = models.CharField(max_length=255)
    flujo_vehicular = models.CharField(max_length=255)
    condicion_roi = models.CharField(max_length=255)
    notas = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class RolUsuario(models.Model):
    id_rol = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    notas = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Direccion(models.Model):
    id_direccion = models.AutoField(primary_key=True)
    name_direccion = models.CharField(max_length=255)
    municipio = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=255)
    pais = models.CharField(max_length=255)
    detalles = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class SpeedLine(models.Model):
    id_speedline = models.AutoField(primary_key=True)
    medicion = models.CharField(max_length=255)
    coords = models.CharField(max_length=255)
    notas = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Vehiculo(models.Model):
    id_vehiculo = models.AutoField(primary_key=True)
    color_vehiculo = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Matricula(models.Model):
    id_matricula = models.AutoField(primary_key=True)
    id_vehiculo = models.ForeignKey('Vehiculo', on_delete=models.CASCADE)
    matricula = models.CharField(max_length=255)
    imagen_matricula = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class TipoInfraccion(models.Model):
    id_tipoinfraccion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    cant_pagar = models.CharField(max_length=255)
    detalles = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Infraccion(models.Model):
    id_infraccion = models.AutoField(primary_key=True)
    id_vehiculo = models.ForeignKey('Vehiculo', on_delete=models.CASCADE)
    id_camara = models.ForeignKey('Camara', on_delete=models.CASCADE)
    fecha_infraccion = models.DateTimeField()
    velocidad_estimada = models.CharField(max_length=255)
    tipo_infraccion = models.ForeignKey('TipoInfraccion', on_delete=models.CASCADE)
    id_videoinfraccion = models.CharField(max_length=255)
    frame_infraccion = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Camara(models.Model):
    id_camara = models.AutoField(primary_key=True)
    nombre_camara = models.CharField(max_length=255)
    url_camara = models.CharField(max_length=255)
    estado_camara = models.CharField(max_length=255)
    frame_rate = models.CharField(max_length=255)
    id_direccion_camara = models.ForeignKey('Direccion', on_delete=models.CASCADE)
    resolucion_camara = models.CharField(max_length=255)
    notas = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class EstadoCamara(models.Model):
    id_camara = models.ForeignKey('Camara', on_delete=models.CASCADE)
    fecha_estado = models.DateTimeField()
    estado_camara = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Video(models.Model):
    id_video = models.AutoField(primary_key=True)
    id_camara = models.ForeignKey('Camara', on_delete=models.CASCADE)
    nombre_video = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField()
    frame_rate = models.CharField(max_length=255)
    resolucion_video = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class ConfiguracionCamara(models.Model):
    id_configuracion = models.AutoField(primary_key=True)
    id_camara = models.ForeignKey('Camara', on_delete=models.CASCADE)
    fecha_configuracion = models.DateTimeField()
    resolucion_salidavideo = models.CharField(max_length=255)
    confianza_vehiculos = models.CharField(max_length=255)
    confianza_matricula = models.CharField(max_length=255)
    confianza_cascos = models.CharField(max_length=255)
    yolo_class = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class YoloClass(models.Model):
    id_class = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    nombre_traducido = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Modelo(models.Model):
    id_modelo = models.AutoField(primary_key=True)
    nombre_modelo = models.CharField(max_length=255)
    tipo_modelo = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField()
    notas = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Multa(models.Model):
    id_multa = models.AutoField(primary_key=True)
    id_infraccion = models.ForeignKey('Infraccion', on_delete=models.CASCADE)
    estado_multa = models.CharField(max_length=255)
    notas = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Logs(models.Model):
    id_log = models.AutoField(primary_key=True)
    tipo_log = models.CharField(max_length=255)
    cambio_detectado = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Notificacion(models.Model):
    id_notificacion = models.AutoField(primary_key=True)
    id_infraccion = models.ForeignKey('Infraccion', on_delete=models.CASCADE)
    id_rol = models.ForeignKey('RolUsuario', on_delete=models.CASCADE)
    estado_notificacion = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField()
    tipo_notificacion = models.CharField(max_length=255)
    fecha_resolucion = models.DateTimeField()
    id_resolucionusuario = models.CharField(max_length=255)

    class Meta:
        app_label = 'code'


class Reporte(models.Model):
    id_reporte = models.AutoField(primary_key=True)
    tipo_reporte = models.CharField(max_length=255)
    nombre_reporte = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField()
    id_camara = models.ForeignKey('Camara', on_delete=models.CASCADE)

    class Meta:
        app_label = 'code'