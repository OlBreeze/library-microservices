from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'birth_date']
    search_fields = ['user__username', 'user__email', 'location']
    list_filter = ['birth_date']
    readonly_fields = ['user']

    fieldsets = (
        ('Користувач', {
            'fields': ('user',)
        }),
        ('Інформація профілю', {
            'fields': ('bio', 'birth_date', 'location', 'avatar')
        }),
    )
