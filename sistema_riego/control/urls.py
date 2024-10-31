from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('activar-riego/', views.activar_riego, name='activar_riego'),
    path('detener-riego/', views.detener_riego, name='detener_riego'),
    path('historial/', views.historial, name='historial'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('registrar_usuario/<str:codigo_serie>/', views.registrar_usuario, name='registrar_usuario'),
    path('login/', views.login_view, name='login'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('register/', views.register, name='register'),
]

