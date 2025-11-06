from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import RegisterView, UserProfileView, ChangePasswordView, UserDetailView, CustomTokenObtainPairView, \
    LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    # path('users/<int:pk>/', UserProfileView.as_view(), name='user-detail'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
# Endpoint для мікросервісів (перевірка користувача)
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
]