"""Admin del módulo DEV."""
from django.contrib import admin
from .models import (
    DevProfile, DevChallenge, DevSubmission,
    DevSnippet, DevLog, DevADR, DevPingLog,
)


@admin.register(DevProfile)
class DevProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'github_handle', 'total_dev_xp', 'current_dev_level', 'focus_mode_active')
    list_filter = ('focus_mode_active',)
    search_fields = ('user__email', 'github_handle')


@admin.register(DevChallenge)
class DevChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'category', 'xp_reward', 'frequency', 'is_active')
    list_filter = ('difficulty', 'category', 'is_active')
    search_fields = ('title',)


@admin.register(DevSubmission)
class DevSubmissionAdmin(admin.ModelAdmin):
    list_display = ('dev_profile', 'challenge', 'status', 'xp_earned', 'created_at')
    list_filter = ('status',)


@admin.register(DevSnippet)
class DevSnippetAdmin(admin.ModelAdmin):
    list_display = ('title', 'dev_profile', 'language', 'is_private', 'created_at')
    list_filter = ('language', 'is_private')


@admin.register(DevLog)
class DevLogAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'status', 'response_time_ms', 'created_at')
    list_filter = ('status',)


@admin.register(DevADR)
class DevADRAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'author', 'created_at')
    list_filter = ('status',)


@admin.register(DevPingLog)
class DevPingLogAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'status_code', 'response_time_ms', 'created_at')
