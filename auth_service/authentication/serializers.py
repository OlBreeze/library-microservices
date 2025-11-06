from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

from .models import UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    """
    Серіалізатор для реєстрації нових користувачів.

    Fields:
        username: Унікальне ім'я користувача
        email: Унікальна email адреса
        password: Пароль (тільки для запису)
        password2: Підтвердження пароля (тільки для запису)
        first_name: Ім'я користувача (опціонально)
        last_name: Прізвище користувача (опціонально)
        bio, birth_date, location, avatar
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(),
                message="Користувач з таким email вже існує")]
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
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Підтвердження пароля'
    )

    # --- Поля для UserProfile (додано) ---
    bio = serializers.CharField(required=False, allow_blank=True, max_length=500)
    birth_date = serializers.DateField(required=False, allow_null=True)
    location = serializers.CharField(required=False, allow_blank=True, max_length=100)
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'bio', 'birth_date', 'location', 'avatar']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        """
        Перевірка співпадіння паролів.

        Args:
            attrs: Словник з атрибутами

        Returns:
            Валідовані атрибути

        Raises:
            ValidationError: Якщо паролі не співпадають
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Паролі не співпадають"
            })
        return attrs

    def create(self, validated_data):
        """
        Створення нового користувача.

        Args:
            validated_data: Валідовані дані

        Returns:
            Створений об'єкт User
        """

        profile_data = {
            'bio': validated_data.pop('bio', ''),
            'birth_date': validated_data.pop('birth_date', None),
            'location': validated_data.pop('location', ''),
            'avatar': validated_data.pop('avatar', None),
        }

        # Видаляємо password2, оскільки воно не є полем моделі User
        validated_data.pop('password2')

        # Використовуємо create_user для правильного хешування пароля
        # 1. Створення об'єкта User
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'], # ✅ Автоматично хешується
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # 2. Створення об'єкта UserProfile
        UserProfile.objects.create(
            user=user,
            **profile_data  # Розпаковуємо дані профілю
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'birth_date', 'location', 'avatar']

class UserSerializer(serializers.ModelSerializer):
    """
    Серіалізатор для відображення повної інформації про користувача, включаючи профіль.
    """
    books_count = serializers.SerializerMethodField()
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'books_count',
            'profile' # ! Додано профіль
        ]
        read_only_fields = ['id', 'is_staff']

    def get_books_count(self, obj):
        """Отримує кількість книг користувача."""
        # Якщо у вас є модель Book, пов'язана з User, це працюватиме.
        # В іншому випадку, повертаємо 0 або коментуємо.
        return 0 # obj.books.count() # Залишаємо заглушку, якщо 'books' не визначено


class ChangePasswordSerializer(serializers.Serializer):
    """
    Серіалізатор для зміни пароля.
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """
        Перевірка співпадіння нових паролів.
        """
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password": "Нові паролі не співпадають"
            })
        return attrs