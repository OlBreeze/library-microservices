"""
Моделі для застосунку.
Цей модуль містить моделі для роботи з  профілями користувачів.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


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


