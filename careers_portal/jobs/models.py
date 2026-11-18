import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

MAX_RESUME_MB = 5

phone_validator = RegexValidator(
    regex=r'^\+?[0-9\-]{10,15}$',
    message='Enter a valid phone number (10-15 digits, optional +).',
)


def validate_resume_size(file):
    if file.size > MAX_RESUME_MB * 1024 * 1024:
        raise ValidationError(
            f'Resume must be {MAX_RESUME_MB} MB or smaller.'
        )


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
        return self.filter(
            is_active=True,
            is_expired=False,
            closing_date__gte=timezone.localdate(),
        )

    def expire_due(self):
        today = timezone.localdate()

        return self.filter(
            is_active=True,
            closing_date__lt=today,
        ).update(
            is_active=False,
            is_expired=True,
        )


class Job(models.Model):

    class JobType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        CONTRACT = 'contract', 'Contract'
        INTERNSHIP = 'internship', 'Internship'

    class SalaryPeriod(models.TextChoices):
        HOUR = 'HOUR', 'Per Hour'
        DAY = 'DAY', 'Per Day'
        WEEK = 'WEEK', 'Per Week'
        MONTH = 'MONTH', 'Per Month'
        YEAR = 'YEAR', 'Per Year'

    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs',
    )

    
    location = models.CharField(max_length=150)

    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.FULL_TIME,
    )

    experience = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g. 0-2 years',
    )

    salary_range = models.CharField(max_length=100, blank=True)

    description = models.TextField()
    responsibilities = models.TextField()
    requirements = models.TextField()

    closing_date = models.DateField()

    
    job_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )

    date_posted = models.DateField(
        null=True,
        blank=True,
    )

    
    street_address = models.CharField(
        max_length=255,
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
    )

    country = models.CharField(
        max_length=2,
        default='IN',
        blank=True,
        help_text='ISO country code, e.g. IN',
    )

    
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    salary_currency = models.CharField(
        max_length=3,
        default='INR',
        blank=True,
    )

    salary_period = models.CharField(
        max_length=10,
        choices=SalaryPeriod.choices,
        blank=True,
    )

    
    is_remote = models.BooleanField(default=False)

    direct_apply = models.BooleanField(
        default=True,
        editable=False,
    )

    
    is_active = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = JobQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()

        errors = {}

       
        if not self.is_remote:
            if not self.city:
                errors['city'] = 'City is required for on-site jobs.'

            if not self.state:
                errors['state'] = 'State is required for on-site jobs.'

            if not self.country:
                errors['country'] = 'Country is required for on-site jobs.'

        
        if (
            self.closing_date
            and self.closing_date < timezone.localdate()
            and not self.is_expired
        ):
            errors['closing_date'] = (
                'Closing date cannot be in the past.'
            )

        
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            errors['salary_max'] = (
                'Maximum salary cannot be less than minimum salary.'
            )

        if errors:
            raise ValidationError(errors)

    @property
    def is_open(self):
        return (
            self.is_active
            and not self.is_expired
            and self.closing_date >= timezone.localdate()
        )

    def save(self, *args, **kwargs):
        today = timezone.localdate()

        # Automatically set the publishing date.
        if self.is_active and not self.date_posted:
            self.date_posted = today

        
        if self.closing_date and self.closing_date < today:
            self.is_expired = True
            self.is_active = False

        
        if not self.is_active:
            self.is_expired = True

        
        self.direct_apply = True

        super().save(*args, **kwargs)

        
        if not self.job_code:
            self.job_code = f'JOB-{1000 + self.pk}'

            type(self).objects.filter(pk=self.pk).update(
                job_code=self.job_code
            )

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

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField()

    phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
    )

    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    cover_letter = models.TextField(blank=True)

    resume = models.FileField(
        upload_to=resume_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx']
            ),
            validate_resume_size,
        ],
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    internal_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_at']
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'email'],
                name='unique_application_per_job_email',
            ),
        ]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.full_name} → {self.job.title}'


class StoredFile(models.Model):
    """Resume files DB mein (Render free pe disk persistent nahi hota)."""

    name = models.CharField(max_length=255, unique=True)
    content = models.BinaryField()

    def __str__(self):
        return self.name
