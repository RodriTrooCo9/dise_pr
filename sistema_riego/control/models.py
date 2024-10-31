from django.db import models
from django.contrib.auth.models import User
class Registro(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)  # Guardará la fecha y hora automáticamente
    temperatura = models.FloatField()  # Campo para la temperatura
    humedad = models.FloatField()      # Campo para la humedad

    def __str__(self):
        return f"{self.fecha}: Temp {self.temperatura}°C, Humedad {self.humedad}%"
class RegistroTemperatura(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True)
    temperatura = models.FloatField()

    def __str__(self):
        return f"{self.fecha_hora} - {self.temperatura}°C"

class UsuarioArduino(models.Model):
    nombre_usuario = models.CharField(max_length=100)
    codigo_arduino = models.CharField(max_length=10, unique=True)  # Código de serie único de Arduino
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_usuario} - {self.codigo_arduino}"
class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    edad = models.IntegerField()
    codigo_serie = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username