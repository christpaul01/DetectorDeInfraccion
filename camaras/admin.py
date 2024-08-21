from django.contrib import admin

# Register your models here.

from .models import Camara, Direccion
# Register your models here.

admin.site.register(Camara)
admin.site.register(Direccion)

