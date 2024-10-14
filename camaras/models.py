from django.db import models
from datetime import datetime


# Create your models here.

class Direccion(models.Model):
    id_direccion = models.AutoField(primary_key=True)
    nombre_direccion = models.CharField(max_length=255, )
    municipio = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=255)
    pais = models.CharField(max_length=255)
    detalles = models.CharField(max_length=255)


class Camara(models.Model):
    id_camara = models.AutoField(primary_key=True)
    nombre_camara = models.CharField(max_length=255)
    url_camara = models.CharField(max_length=255)
    estado_camara = models.CharField(max_length=25)
    frame_rate = models.CharField(max_length=25)
    frame_count = models.IntegerField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    video_length = models.IntegerField()
    time_video = models.CharField(max_length=25)
    id_direccion_camara = models.ForeignKey('Direccion', on_delete=models.CASCADE, blank=True, null=True)
    resolucion_camara = models.CharField(max_length=255)
    notas = models.CharField(max_length=255)
    first_frame_base64 = models.TextField(blank=True, null=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, blank=True, null=True)



class ROI(models.Model):
    TIPO_ROI_CHOICES = [
        ('N', 'Normal'),
        ('P', 'Prohibido'),
    ]
    ESTADO_ROI_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
    ]

    id_roi = models.AutoField(primary_key=True)
    id_camara = models.ForeignKey(Camara, on_delete=models.CASCADE)
    estado_roi = models.CharField(max_length=1, choices=ESTADO_ROI_CHOICES, default='A')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    tipo_roi = models.CharField(max_length=1, choices=TIPO_ROI_CHOICES, default='N')
    coordenadas = models.CharField(max_length=100, blank= False, null= False)
    flujo_vehicular = models.IntegerField(null=True, blank=True)
    condicion_roi = models.CharField(max_length=255, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)

class Infraccion(models.Model):
    id_infraccion = models.AutoField(primary_key=True)
    id_vehiculo = models.CharField(max_length=25)
    id_tipo_vehiculo = models.ForeignKey('TipoVehiculo', on_delete=models.CASCADE)
    id_camara = models.ForeignKey('Camara', on_delete=models.CASCADE)
    fecha_infraccion = models.DateTimeField()
    velocidad_estimada = models.FloatField()
    tipo_infraccion = models.ForeignKey('TipoInfraccion', on_delete=models.CASCADE)
    id_videoinfraccion = models.CharField(max_length=255)
    frame_inicio = models.CharField(max_length=25)
    frame_final = models.CharField(max_length=25)
    estado_infraccion = models.CharField(max_length=25)
    revision_infraccion = models.CharField(max_length=25)
    notas = models.CharField(max_length=255)

class TipoVehiculo(models.Model):
    id_tipo_vehiculo = models.AutoField(primary_key=True)
    nombre_tipo_vehiculo = models.CharField(max_length=255)
    detalles = models.CharField(max_length=255)

class TipoInfraccion(models.Model):
    id_tipo_infraccion = models.AutoField(primary_key=True)
    nombre_tipo_infraccion = models.CharField(max_length=255)
    cant_pagar = models.CharField(max_length=255)
    detalles = models.CharField(max_length=255)

class Matricula:
    id_matricula = models.AutoField(primary_key=True)
    id_vehiculo = models.ForeignKey('Vehiculo', on_delete=models.CASCADE)
    matricula = models.CharField(max_length=255)
    imagen_matricula = models.ImageField(upload_to='matriculas')

class Video(models.Model):
    id_video = models.AutoField(primary_key=True)
    id_camara = models.ForeignKey('Camara', on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    video = models.FileField(upload_to='videos')


def __str__(self):
    texto: "{0}"
    return texto.format(self.id_nombre_camara)
