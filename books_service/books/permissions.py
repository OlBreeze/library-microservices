from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Дозвіл, який дозволяє тільки адміністраторам виконувати небезпечні методи.

    - GET, HEAD, OPTIONS доступні всім автентифікованим користувачам
    - POST, PUT, PATCH доступні всім автентифікованим користувачам
    - DELETE доступний тільки адміністраторам
    """

    def has_permission(self, request, view):
        """
        Перевірка дозволу на рівні запиту.

        Args:
            request: HTTP запит
            view: View, який обробляє запит

        Returns:
            True, якщо дозвіл надано, False - інакше
        """
        # # Дозволяємо безпечні методи всім автентифікованим користувачам
        # if request.method in permissions.SAFE_METHODS:
        #     return request.user and request.user.is_authenticated
        #
        # # Дозволяємо POST, PUT, PATCH всім автентифікованим користувачам
        # if request.method in ['POST', 'PUT', 'PATCH']:
        #     return request.user and request.user.is_authenticated

        # Разрешаем всё, кроме удаления
        if request.user.is_authenticated and (
                request.method in permissions.SAFE_METHODS or request.method in ['POST', 'PUT', 'PATCH']
        ):
            return True

        # DELETE дозволений тільки адміністраторам
        if request.method == 'DELETE':
            return request.user and request.user.is_staff

        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Дозвіл, який дозволяє редагувати об'єкт тільки його власнику або адміністратору.
    """

    def has_object_permission(self, request, view, obj):
        """
        Перевірка дозволу на рівні об'єкта.

        Args:
            request: HTTP запит
            view: View, який обробляє запит
            obj: Об'єкт, до якого здійснюється доступ

        Returns:
            True, якщо дозвіл надано, False - інакше
        """
        # Дозволяємо безпечні методи всім
        if request.method in permissions.SAFE_METHODS:
            return True

        # DELETE дозволений тільки адміністраторам
        if request.method == 'DELETE':
            return request.user.is_staff

        # PUT, PATCH дозволені власнику або адміністратору
        return obj.user == request.user or request.user.is_staff
