"""
Моделі для застосунку.
Цей модуль містить моделі для роботи з  профілями користувачів.
"""
import re

from django.contrib.auth.password_validation import validate_password
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


def validate_image_size(image):
    """Валідація розміру зображення (максимум 2 МБ)"""
    file_size = image.size
    limit_mb = 2
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Максимальний розмір файлу {limit_mb} МБ")


class UserProfile(models.Model):
    """
      Розширення моделі користувача додатковими полями.

      Attributes:
          user (User): Зв'язок один-до-одного з вбудованою моделлю User
          bio (str): Біографія
          birth_date (str): Дата народження
      """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Користувач'
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name="Біографія")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата народження")
    location = models.CharField(max_length=100, blank=True, verbose_name="Місце проживання")
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        validators=[validate_image_size],
        verbose_name="Аватар"
    )

    class Meta:
        verbose_name = "Профіль користувача"
        verbose_name_plural = "Профілі користувачів"

    def __str__(self):
        return f"Профіль {self.user.username}"


class RegisterSerializer(serializers.ModelSerializer):
    """Серіалізатор реєстрації з розширеною валідацією."""

    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Користувач з таким email вже існує"
            )
        ]
    )

    username = serializers.CharField(
        required=True,
        min_length=3,
        max_length=150,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Користувач з таким username вже існує"
            )
        ]
    )

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        min_length=8
    )

    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Підтвердження пароля'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate_username(self, value):
        """
        Валідація username:
        - Тільки літери, цифри, _, -
        - Без пробілів
        - Мінімум 3 символи
        """
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError(
                "Username може містити тільки літери, цифри, _ та -"
            )

        if value.lower() in ['admin', 'root', 'superuser', 'administrator']:
            raise serializers.ValidationError(
                "Цей username зарезервований системою"
            )

        return value

    def validate_email(self, value):
        """
        Валідація email:
        - Правильний формат
        - Не з тимчасових email сервісів
        """
        # Список заборонених доменів
        blocked_domains = [
            'tempmail.com',
            '10minutemail.com',
            'guerrillamail.com',
            'mailinator.com'
        ]

        domain = value.split('@')[1].lower()
        if domain in blocked_domains:
            raise serializers.ValidationError(
                "Тимчасові email адреси не дозволені"
            )

        return value.lower()

    def validate(self, attrs):
        """Перевірка співпадіння паролів."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Паролі не співпадають"
            })
        return attrs

    def create(self, validated_data):
        """Створення користувача з хешованим паролем."""
        validated_data.pop('password2')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],  # ✅ Автоматично хешується
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user