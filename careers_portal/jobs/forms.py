from django import forms
from .models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['full_name', 'email', 'phone', 'linkedin_url',
                  'portfolio_url', 'cover_letter', 'resume']
        labels = {
            'full_name': 'Full Name',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'linkedin_url': 'LinkedIn URL (optional)',
            'portfolio_url': 'Portfolio URL (optional)',
            'cover_letter': 'Cover Letter',
            'resume': 'Upload Resume (PDF, DOC, DOCX, max 5 MB)',
        }
        widgets = {'cover_letter': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, job=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.job = job
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['resume'].widget.attrs['accept'] = '.pdf,.doc,.docx'

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if self.job and Application.objects.filter(job=self.job, email__iexact=email).exists():
            raise forms.ValidationError('You have already applied for this position with this email.')
        return email
