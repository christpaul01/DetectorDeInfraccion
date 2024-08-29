from django.db import models


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
    id_direccion_camara = models.ForeignKey('Direccion', on_delete=models.CASCADE, blank=True, null=True)
    resolucion_camara = models.CharField(max_length=255)
    notas = models.CharField(max_length=255)


# class SpeedLine(models.Model):
#     id_speedline = models.AutoField(primary_key=True)
#     medicion = models.CharField(max_length=255)
#     coords = models.CharField(max_length=255)
#     notas = models.CharField(max_length=255)


class Infraccion(models.Model):
    id_infraccion = models.AutoField(primary_key=True)
    id_vehiculo = models.CharField(max_length=25)
    id_tipo_vehiculo = models.ForeignKey('TipoVehiculo', on_delete=models.CASCADE)
    id_camara = models.ForeignKey('Camara', on_delete=models.CASCADE)
    fecha_infraccion = models.DateTimeField()
    velocidad_estimada = models.FloatField()
    tipo_infraccion = models.ForeignKey('TipoInfraccion', on_delete=models.CASCADE)
    id_videoinfraccion = models.CharField(max_length=255)
    frame_infraccion = models.CharField(max_length=255)

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



def __str__(self):
    texto: "{0}"
    return texto.format(self.id_nombre_camara)
