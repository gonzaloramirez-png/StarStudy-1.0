"""Admin de habits: registro de Habit y HabitCompletion en panel de administración."""
from django.contrib import admin
from .models import Habit, HabitCompletion


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'level', 'created_at']
    list_filter = ['category']
    search_fields = ['title', 'user__email']


@admin.register(HabitCompletion)
class HabitCompletionAdmin(admin.ModelAdmin):
    list_display = ['habit', 'date', 'completed_at']
