"""Formularios del módulo DEV."""
from django import forms
from .models import DevChallenge, DevSnippet, DevADR


class DevChallengeForm(forms.ModelForm):
    class Meta:
        model = DevChallenge
        fields = ['title', 'description', 'difficulty', 'category', 'initial_code', 'test_cases', 'xp_reward', 'frequency']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'initial_code': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 6}),
            'test_cases': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 4, 'placeholder': '[{"input": "...", "expected": "..."}]'}),
            'xp_reward': forms.NumberInput(attrs={'class': 'form-control', 'min': 25, 'max': 100}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
        }


class DevSubmissionForm(forms.Form):
    submitted_code = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control font-monospace',
            'rows': 10,
            'placeholder': 'Escribí tu solución aquí...',
        }),
        label='Código',
    )


class DevSnippetForm(forms.ModelForm):
    class Meta:
        model = DevSnippet
        fields = ['title', 'code', 'language', 'tags', 'is_private']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 8}),
            'language': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'python, javascript, sql...'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'docker, sql, regex (separar con coma)'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_tags(self):
        raw = self.cleaned_data.get('tags', '')
        if isinstance(raw, str):
            return [t.strip() for t in raw.split(',') if t.strip()]
        return raw


class DevADRForm(forms.ModelForm):
    class Meta:
        model = DevADR
        fields = ['title', 'context', 'decision', 'consequences', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'context': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'decision': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'consequences': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
