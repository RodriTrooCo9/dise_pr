from django.contrib import admin
from .models import Registro
from .models import RegistroTemperatura
from .models import UsuarioArduino

admin.site.register(Registro)
admin.site.register(RegistroTemperatura)
admin.site.register(UsuarioArduino)