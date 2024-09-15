from django.db import models


# Create your models here.

class Direccion(models.Model):
    id_direccion = models.AutoField(primary_key=True)
    nombre_direccion = models.CharField(max_length=255)
    municipio = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=255)
    pais = models.CharField(max_length=255)
    detalles = models.CharField(max_length=255)


class Camara(models.Model):
    id_camara = models.AutoField(primary_key=True)
    nombre_camara = models.CharField(max_length=255)
    url_camara = models.CharField(max_length=255)
    estado_camara = models.CharField(max_length=255)
    frame_rate = models.CharField(max_length=255)
    id_direccion_camara = models.ForeignKey('Direccion', on_delete=models.CASCADE, blank=True, null=True)
    resolucion_camara = models.CharField(max_length=255)
    notas = models.CharField(max_length=255)


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre_usuario = models.CharField(max_length=100)
    clave_usuario = models.CharField(max_length=100)
    rol_usuario = models.CharField(max_length=10)

class Video(models.Model):
    caption=models.CharField(max_length=100)
    video=models.FileField(upload_to="video/%y")
    def __str__(self):
       return self.caption

def __str__(self):
    texto: "{0}"
    return texto.format(self.id_nombre_camara)
