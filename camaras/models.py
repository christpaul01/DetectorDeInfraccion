from django.db import models

# Create your models here.

class Camara(models.Model):
    id_camara = models.AutoField(primary_key=True)
    nombre_camara = models.CharField(max_length=255)
    url_camara = models.CharField(max_length=255)
    estado_camara = models.CharField(max_length=255)
    frame_rate = models.CharField(max_length=255)
    id_direccion_camara = models.ForeignKey('Direccion', on_delete=models.CASCADE)
    resolucion_camara = models.CharField(max_length=255)
    notas = models.CharField(max_length=255)
