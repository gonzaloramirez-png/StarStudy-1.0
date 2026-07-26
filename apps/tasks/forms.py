"""Formularios de tasks: creación de tareas, comentarios y snippets.

- TaskForm: formulario con título, descripción, importancia, deadline, archivo adjunto,
  y assigned_to (limitado a estudiantes si el usuario es profesor/personal/programador).
- CommentForm: textarea para agregar comentarios.
- CommentSnippetForm: formulario para crear/editar snippets de comentarios reutilizables.
"""
from django import forms
from django.conf import settings
from .models import Task, Comment, CommentSnippet
from apps.accounts.models import User


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'importance', 'deadline', 'assigned_to', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'importance': forms.Select(attrs={'class': 'form-select'}),
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['deadline'].input_formats = ['%Y-%m-%dT%H:%M']
        if user and user.role != User.Role.STUDENT:
            self.fields['assigned_to'].queryset = User.objects.filter(role=User.Role.STUDENT)
        elif user:
            self.fields.pop('assigned_to', None)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Escribí un comentario...'}),
        }


class CommentSnippetForm(forms.ModelForm):
    class Meta:
        model = CommentSnippet
        fields = ['title', 'content', 'category', 'is_shared']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: "Buen trabajo", "Mejorar redacción"'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Usa {student_name} para personalizar...'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: elogio, mejora, instrucción'}),
            'is_shared': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }