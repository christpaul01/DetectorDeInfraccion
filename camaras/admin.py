from django.contrib import admin
<<<<<<<<< Temporary merge branch 1
from .models import Camara, Direccion
||||||||| aebe305

=========
from .models import Camara

>>>>>>>>> Temporary merge branch 2
# Register your models here.
<<<<<<<<< Temporary merge branch 1

admin.site.register(Camara)
admin.site.register(Direccion)
||||||||| aebe305
=========

class CamaraAdmin(admin.ModelAdmin):
  list_display = ("id_camara", "nombre_camara",)


admin.site.register(Camara, CamaraAdmin)
>>>>>>>>> Temporary merge branch 2
