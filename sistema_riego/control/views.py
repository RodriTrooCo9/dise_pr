import serial
import time
import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Registro, UsuarioArduino  # Importamos el modelo UsuarioArduino
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib import messages
from .models import PerfilUsuario  # Asumiendo que tienes un modelo personalizado para el perfil de usuario
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

# Variables para múltiples Arduinos
arduinos = {}
temperatura = "--"
humedad = "--"

# Configuración de OpenWeatherMap
API_KEY = 'c8b804d8292e6bf17f3c982422c5a28e'
CIUDAD = 'lapaz'

def conectar_arduino(codigo_serie):
    """Intenta conectar un Arduino por su código de serie y lo almacena en el diccionario."""
    global arduinos
    try:
        if codigo_serie not in arduinos:  # Si no está registrado, lo conectamos
            puerto = 'COM' + codigo_serie[-1]  # Asumimos que cada código se refiere a un puerto diferente
            arduino = serial.Serial(puerto, 9600, timeout=1)
            time.sleep(2)  # Esperar a que el puerto se estabilice
            arduinos[codigo_serie] = arduino
            print(f"Arduino con código {codigo_serie} conectado.")
        return arduinos[codigo_serie]
    except serial.SerialException as e:
        print(f"Error al conectar con Arduino {codigo_serie}: {e}")
        return None

def obtener_temperatura_api():
    """Obtiene la temperatura actual desde la API de OpenWeatherMap."""
    url = f'http://api.openweathermap.org/data/2.5/weather?q={CIUDAD}&appid={API_KEY}&units=metric&lang=es'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temperatura_api = data['main']['temp']
        return temperatura_api
    return None

@login_required(login_url='/login/')  # Redirigir al login si no está autenticado
def index(request):
    global temperatura, humedad

    # Simulación: códigos de serie que se leen desde el puerto
    codigos_arduino = ['001', '002', '003', '004']  # Ejemplo de códigos de serie

    for codigo in codigos_arduino:
        arduino = conectar_arduino(codigo)

        if arduino is not None:
            try:
                if arduino.in_waiting > 0:
                    datos = arduino.readline().decode('utf-8').strip()
                    if "Temperatura" in datos:
                        temperatura = datos.split(":")[1].strip()
                    elif "Humedad" in datos:
                        humedad = datos.split(":")[1].strip()
            except Exception as e:
                print(f"Error al leer datos del Arduino {codigo}: {e}")

        # Verificar si el código de Arduino está registrado
        usuario_arduino = UsuarioArduino.objects.filter(codigo_arduino=codigo).first()

        if not usuario_arduino:
            # Si no está registrado, redirigir a una página para registrar un nuevo usuario
            return redirect('registrar_usuario', codigo_serie=codigo)


    # Obtener la temperatura de la API del clima
    temperatura_api = obtener_temperatura_api()

    context = {
        'temperatura': temperatura_api if temperatura == "--" else temperatura,
        'humedad': humedad,
        'arduinos_conectados': [codigo for codigo in codigos_arduino if codigo in arduinos],
    }

    return render(request, 'control/index.html', context)



def registrar_usuario(request, codigo_serie):
    """Vista para registrar un nuevo usuario asociado a un código de Arduino."""
    if request.method == "POST":
        nombre_usuario = request.POST.get("nombre_usuario")
        if nombre_usuario:
            # Crear un nuevo usuario asociado al código de Arduino
            UsuarioArduino.objects.create(nombre_usuario=nombre_usuario, codigo_arduino=codigo_serie)
            return redirect('index')  # Redirigir a la página principal después del registro

    return render(request, 'control/iniciar_sesion.html', {'codigo_serie': codigo_serie})
@login_required
def activar_riego(request, codigo_serie):
    arduino = conectar_arduino(codigo_serie)
    if arduino:
        arduino.write(b'r')
        return JsonResponse({'status': f'Riego activado en Arduino {codigo_serie}'})
    return JsonResponse({'status': f'Arduino {codigo_serie} no conectado'})
@login_required
def detener_riego(request, codigo_serie):
    arduino = conectar_arduino(codigo_serie)
    if arduino:
        arduino.write(b's')
        return JsonResponse({'status': f'Riego detenido en Arduino {codigo_serie}'})
    return JsonResponse({'status': f'Arduino {codigo_serie} no conectado'})


@login_required
def historial(request):
    registros = Registro.objects.all()
    context = {'registros': registros}
    return render(request, 'control/historial.html', context)

@login_required
def estadisticas(request):
    registros = Registro.objects.all()

    # Gráfico de barras
    fechas = [registro.fecha.strftime('%d-%m %H:%M') for registro in registros]
    temperaturas = [registro.temperatura for registro in registros]
    humedades = [registro.humedad for registro in registros]

    if len(fechas) > 0:  # Verificar que haya registros
        plt.figure(figsize=(10, 5))
        plt.bar(fechas, temperaturas, color='b', label='Temperatura')
        plt.bar(fechas, humedades, color='g', label='Humedad', alpha=0.7)
        plt.xticks(rotation=45)
        plt.xlabel('Fecha y Hora')
        plt.ylabel('Medidas')
        plt.title('Gráfica de Barras de Temperatura y Humedad')
        plt.legend()

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_barras = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
    else:
        image_barras = None

    # Gráfico de pastel
    bajas = sum(1 for registro in registros if registro.temperatura < 15)
    medias = sum(1 for registro in registros if 15 <= registro.temperatura < 25)
    altas = sum(1 for registro in registros if registro.temperatura >= 25)

    total = bajas + medias + altas

    if total > 0:
        plt.figure(figsize=(7, 7))
        plt.pie([bajas, medias, altas], labels=['Bajas (<15°C)', 'Medias (15-25°C)', 'Altas (>25°C)'],
                colors=['#ff9999', '#66b3ff', '#99ff99'], autopct='%1.1f%%', startangle=90)
        plt.title('Distribución de Temperaturas')

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_pastel = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
    else:
        image_pastel = None

    context = {
        'grafica_barras': image_barras,
        'grafica_pastel': image_pastel
    }
    return render(request, 'control/estadisticas.html', context)
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            # Verifica si el usuario existe con ese correo
            user = User.objects.get(email=email)
            # Envía un correo con las instrucciones para restablecer la contraseña
            send_mail(
                'Restablecimiento de Contraseña',
                f'Hola {user.username},\n\nHaz clic en el siguiente enlace para restablecer tu contraseña: http://tu_dominio.com/reset-password/{user.username}',
                'tu_correo@gmail.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Se ha enviado un correo para restablecer tu contraseña.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'No se ha encontrado ningún usuario con ese correo.')
    return render(request, 'control/forgot_password.html')

def register(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        apellido = request.POST['apellido']
        edad = request.POST['edad']
        email = request.POST['email']
        codigo_serie = request.POST['codigo_serie']
        password = request.POST['password']

        # Verifica si el correo ya está registrado
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo ya está registrado.')
            return redirect('register')

        # Crea un nuevo usuario
        user = User.objects.create_user(username=email, password=password, email=email)
        user.first_name = nombre
        user.last_name = apellido
        user.save()

        # Crea un perfil de usuario relacionado
        perfil = PerfilUsuario(user=user, edad=edad, codigo_serie=codigo_serie)
        perfil.save()

        messages.success(request, 'Usuario registrado exitosamente.')
        return redirect('login')

    return render(request, 'control/register.html')
def login_view(request):
    if request.method == 'POST':
        username = request.POST['nombre_usuario']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')  # Redirige a la página principal después de iniciar sesión
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos')
    return render(request, 'control/login.html')
