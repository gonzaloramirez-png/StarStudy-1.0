"""Admin de gamification: Quiz, Preguntas, Intentos."""
from django.contrib import admin
from .models import Quiz, QuizQuestion, QuizAttempt


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1
    fields = ['order', 'text', 'type', 'points']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'created_by', 'xp_reward', 'passing_score', 'is_active', 'created_at']
    list_filter = ['course', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    inlines = [QuizQuestionInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'order', 'text', 'type', 'points']
    list_filter = ['quiz', 'type']
    search_fields = ['text']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'student', 'score', 'xp_earned', 'passed', 'status', 'submitted_at']
    list_filter = ['quiz', 'status', 'passed', 'submitted_at']
    search_fields = ['student__email', 'quiz__title']
    readonly_fields = ['student', 'quiz', 'answers', 'submitted_at', 'score', 'xp_earned', 'passed', 'status']