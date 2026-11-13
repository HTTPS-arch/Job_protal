from django import forms
from jobs.models import Application

class ApplicationForm(forms.ModelForm):

    class Meta:
        model = Application
        fields = [
            'full_name',
            'email',
            'phone',
            'resume',
            'cover_letter',
            'portfolio_url',
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Enter your full name'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Enter your phone number'
            }),
            'cover_letter': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Write your cover letter'
            }),
        }
