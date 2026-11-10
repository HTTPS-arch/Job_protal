from django.db import models
from django.utils.text import slugify

class Job(models.Model):

    JOB_TYPE_CHOICES = [
        ('Full Time', 'Full Time'),
        ('Part Time', 'Part Time'),
        ('Internship', 'Internship'),
        ('Contract', 'Contract'),
    ]

    EXPERIENCE_CHOICES = [
        ('Fresher', 'Fresher'),
        ('1-3 Years', '1-3 Years'),
        ('3-5 Years', '3-5 Years'),
        ('5+ Years', '5+ Years'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=150)
    job_type = models.CharField(
        max_length=50,
        choices=JOB_TYPE_CHOICES
    )
    experience_level = models.CharField(
        max_length=50,
        choices=EXPERIENCE_CHOICES
    )
    salary_range = models.CharField(
        max_length=100, blank=True
    )
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField()
    closing_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Application(models.Model):

    STATUS_CHOICES = [
        ('New', 'New'),
        ('Reviewed', 'Reviewed'),
        ('Shortlisted', 'Shortlisted'),
        ('Interview', 'Interview'),
        ('Offered', 'Offered'),
        ('Rejected', 'Rejected'),
    ]

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField(blank=True)
    portfolio_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='New'
    )
    internal_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.job.title}"
