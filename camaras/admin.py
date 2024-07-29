from django.contrib import admin
from .models import Camara

# Register your models here.

class CamaraAdmin(admin.ModelAdmin):
  list_display = ("id_camara", "nombre_camara",)


admin.site.register(Camara, CamaraAdmin)