from django.urls import path

from . import views

app_name = 'KeyServApp_api'

urlpatterns = [
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/me/', views.MeView.as_view(), name='me'),
    path('publicaciones/', views.PublicacionListView.as_view(), name='publicaciones-list'),
    path('publicaciones/<int:pk>/', views.PublicacionDetailView.as_view(), name='publicaciones-detail'),
]
