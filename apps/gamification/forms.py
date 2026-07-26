"""Formularios de gamification: Quiz, Preguntas, Tips, Rewards, Badges."""
from django import forms
from apps.gamification.models import Quiz, QuizQuestion, TipTransaction, Reward, Badge
from apps.courses.models import Course, TeacherCourse, StudentCourse
from apps.accounts.models import User


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'course', 'xp_reward', 'passing_score', 'time_limit', 'max_attempts', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'xp_reward': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 500}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Minutos (0 = sin límite)'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': '0 = ilimitado'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['course'].queryset = Course.objects.filter(
                teacher_assignments__teacher=user,
                status=Course.Status.ACTIVE
            ).distinct()


class QuizQuestionForm(forms.ModelForm):
    class Meta:
        model = QuizQuestion
        fields = ['text', 'type', 'points', 'explanation', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Texto de la pregunta'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 10}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Explicación (opcional)'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class TipForm(forms.ModelForm):
    class Meta:
        model = TipTransaction
        fields = ['student', 'course', 'xp_amount', 'reason', 'custom_reason']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'xp_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 50, 'value': 5}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'custom_reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Motivo personalizado (si elegiste "Otro")'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Solo estudiantes de los cursos del profesor
            self.fields['student'].queryset = User.objects.filter(
                role=User.Role.STUDENT,
                student_courses__course__teacher_assignments__teacher=user,
                student_courses__status=StudentCourse.Status.ACTIVE
            ).distinct()

            self.fields['course'].queryset = Course.objects.filter(
                teacher_assignments__teacher=user,
                status=Course.Status.ACTIVE
            ).distinct()


class RewardForm(forms.ModelForm):
    class Meta:
        model = Reward
        fields = ['course', 'name', 'description', 'type', 'xp_cost', 'icon', 'max_claims', 'is_active']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: "1 día extra de plazo"'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'xp_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-gift, bi-calendar-plus, bi-skip-forward'}),
            'max_claims': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'value': 0, 'help_text': '0 = ilimitado'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['course'].queryset = Course.objects.filter(
                teacher_assignments__teacher=user,
                status=Course.Status.ACTIVE
            ).distinct()


class BadgeForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = ['name', 'description', 'category', 'icon', 'color', 'xp_reward', 'is_secret']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: "Estrella Colaborativa"'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: bi-star-fill, bi-trophy-fill, bi-emoji-sunglasses'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'gold, silver, bronze, primary, success, danger'}),
            'xp_reward': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'value': 10}),
            'is_secret': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }