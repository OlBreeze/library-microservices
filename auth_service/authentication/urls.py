from django.urls import path
from .views import RegisterView, UserProfileView, ChangePasswordView, UserDetailView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    # path('users/<int:pk>/', UserProfileView.as_view(), name='user-detail'),
# Endpoint для мікросервісів (перевірка користувача)
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
]