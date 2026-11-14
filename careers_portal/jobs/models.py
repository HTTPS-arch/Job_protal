import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

MAX_RESUME_MB = 5

phone_validator = RegexValidator(
    regex=r'^\+?[0-9\s\-]{10,15}$',
    message='Enter a valid phone number (10-15 digits, optional +).',
)


def validate_resume_size(file):
    if file.size > MAX_RESUME_MB * 1024 * 1024:
        raise ValidationError(f'Resume must be {MAX_RESUME_MB} MB or smaller.')


def resume_upload_path(instance, filename):
    ext = Path(filename).suffix.lower()
    now = timezone.now()
    return f'resumes/{now:%Y}/{now:%m}/{uuid.uuid4().hex}{ext}'


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class JobQuerySet(models.QuerySet):
    def open(self):
        return self.filter(is_active=True, closing_date__gte=timezone.localdate())


class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        CONTRACT = 'contract', 'Contract'
        INTERNSHIP = 'internship', 'Internship'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs'
    )
    location = models.CharField(max_length=150)
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    experience = models.CharField(max_length=100, blank=True, help_text='e.g. 0-2 years')
    salary_range = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    responsibilities = models.TextField()
    requirements = models.TextField()
    closing_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = JobQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        return self.is_active and self.closing_date >= timezone.localdate()

    def get_absolute_url(self):
        return reverse('job_detail', kwargs={'slug': self.slug})


class Application(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        REVIEWED = 'reviewed', 'Reviewed'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        INTERVIEW = 'interview', 'Interview'
        OFFERED = 'offered', 'Offered'
        REJECTED = 'rejected', 'Rejected'

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, validators=[phone_validator])
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(
        upload_to=resume_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
            validate_resume_size,
        ],
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    internal_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_at']
        constraints = [
            models.UniqueConstraint(fields=['job', 'email'], name='unique_application_per_job_email'),
        ]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()  # duplicate check case-insensitive rahe
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.full_name} → {self.job.title}'
    
class StoredFile(models.Model):
    """Resume files DB mein (Render free pe disk persistent nahi hota)."""
    name = models.CharField(max_length=255, unique=True)
    content = models.BinaryField()

    def __str__(self):
        return self.name