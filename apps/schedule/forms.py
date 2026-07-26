"""Formularios de schedule: horarios, semáforo de riesgo, tutorías.

- ScheduleEntryForm: formulario para crear/editar entradas de horario.
  Valida que hora fin > hora inicio y que no se superponga con otra entrada existente.
- RiskTrafficLightForm: formulario para actualizar semáforo de riesgo.
- TutoringSlotForm: formulario para crear/editar slots de tutoría.
"""
from django import forms
from .models import ScheduleEntry, RiskTrafficLight, TutoringSlot
from apps.accounts.models import User


class ScheduleEntryForm(forms.ModelForm):
    class Meta:
        model = ScheduleEntry
        fields = ['day', 'start_time', 'end_time', 'title', 'entry_type']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Matemáticas'}),
            'entry_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self._user = user
        super().__init__(*args, **kwargs)
        if user and user.role == User.Role.PROGRAMMER:
            self.fields['entry_type'].choices = [
                ('SUBJECT', 'Materia'),
                ('BREAK', 'Descanso'),
                ('LUNCH', 'Comida'),
            ]

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
        day = cleaned_data.get('day')
        if start_time and end_time and day and self._user:
            overlaps = ScheduleEntry.objects.filter(
                user=self._user,
                day=day,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
            if self.instance.pk:
                overlaps = overlaps.exclude(pk=self.instance.pk)
            if overlaps.exists():
                raise forms.ValidationError('Este horario se superpone con otro existente.')
        return cleaned_data


class RiskTrafficLightForm(forms.ModelForm):
    class Meta:
        model = RiskTrafficLight
        fields = ['level', 'reasons', 'auto_calculated']
        widgets = {
            'level': forms.Select(attrs={'class': 'form-select'}),
            'reasons': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Motivos del nivel de riesgo...'}),
            'auto_calculated': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TutoringSlotForm(forms.ModelForm):
    class Meta:
        model = TutoringSlot
        fields = ['day', 'start_time', 'end_time', 'location', 'max_students']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Aula, enlace Meet/Zoom, etc.'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
        return cleaned_data