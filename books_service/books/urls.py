from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet

# Автоматична генерація URL через Router
router = DefaultRouter()
router.register(r'', BookViewSet, basename='book')

urlpatterns = [
    path('', include(router.urls)),
]