import csv
from pathlib import Path

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import FileResponse, Http404, HttpResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import slugify

from .models import Application, Department, Job

admin.site.site_header = 'Avalanche High-Tech Enterprises HR Panel'
admin.site.site_title = 'Avalanche HR'
admin.site.index_title = 'Careers Management'


class ApplicationInline(admin.TabularInline):
    model = Application
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ('full_name', 'email', 'phone', 'status', 'applied_at')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ('name',)



@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'job_code',
        'department',
        'location',
        'job_type',
        'closing_date',
        'is_active',
        'is_expired',
        'application_count',
    )

    list_filter = (
        'job_type',
        'location',
        'is_active',
        'is_expired',
        'is_remote',
    )

    search_fields = (
        'title',
        'job_code',
        'description',
        'location',
        'city',
        'state',
    )

    prepopulated_fields = {'slug': ('title',)}
    inlines = [ApplicationInline]

    actions = ['close_jobs', 'reopen_jobs']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'slug',
                'department',
                'location',
                'job_type',
                'experience',
                'description',
                'responsibilities',
                'requirements',
            )
        }),
        ('Google for Jobs - Location', {
            'fields': (
                'is_remote',
                'street_address',
                'city',
                'state',
                'postal_code',
                'country',
            )
        }),
        ('Google for Jobs - Salary', {
            'fields': (
                'salary_min',
                'salary_max',
                'salary_currency',
                'salary_period',
                'salary_range',
            )
        }),
        ('Google for Jobs - Publishing', {
            'fields': (
                'job_code',
                'date_posted',
                'closing_date',
                'direct_apply',
            )
        }),
        ('Job Status', {
            'fields': (
                'is_active',
                'is_expired',
            )
        }),
        ('System Information', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    readonly_fields = (
        'job_code',
        'date_posted',
        'direct_apply',
        'is_expired',
        'created_at',
        'updated_at',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            app_count=Count('applications')
        )

    @admin.display(description='Applications', ordering='app_count')
    def application_count(self, obj):
        return obj.app_count

    @admin.action(description='Close selected jobs')
    def close_jobs(self, request, queryset):
        count = queryset.update(
            is_active=False,
            is_expired=True,
        )

        self.message_user(
            request,
            f'{count} job(s) closed and marked expired.',
            messages.SUCCESS,
        )

    @admin.action(description='Reopen selected jobs')
    def reopen_jobs(self, request, queryset):
        today = timezone.localdate()

        eligible_jobs = queryset.filter(closing_date__gte=today)

        count = eligible_jobs.update(
            is_active=True,
            is_expired=False,
        )

        skipped = queryset.count() - count

        self.message_user(
            request,
            f'{count} job(s) reopened. {skipped} overdue job(s) skipped.',
            messages.WARNING if skipped else messages.SUCCESS,
        )



def _safe(value):
    """Excel formula injection se bachne ke liye."""
    value = str(value)
    return "'" + value if value[:1] in ('=', '+', '-', '@') else value


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job', 'email', 'phone', 'status',
                    'applied_at', 'resume_link')
    list_filter = ('job', 'status')
    search_fields = ('full_name', 'email', 'job__title')
    actions = ['export_csv']

    # Sirf status aur internal_notes editable
    fields = ('job', 'full_name', 'email', 'phone', 'linkedin_url',
              'portfolio_url', 'cover_letter', 'resume_link', 'applied_at',
              'status', 'internal_notes')
    readonly_fields = ('job', 'full_name', 'email', 'phone', 'linkedin_url',
                       'portfolio_url', 'cover_letter', 'resume_link', 'applied_at')

    def has_add_permission(self, request):
        return False  # applications sirf public site se aati hain

    # --- Resume download (sirf logged-in staff ke liye) ---
    def get_urls(self):
        custom = [
            path('<int:pk>/resume/',
                 self.admin_site.admin_view(self.download_resume),
                 name='jobs_application_resume'),
        ]
        return custom + super().get_urls()  # custom pehle, warna admin ka catch-all pakad leta hai

    def download_resume(self, request, pk):
        obj = self.get_object(request, str(pk))
        if obj is None or not obj.resume:
            raise Http404('Resume not found')
        if not self.has_view_permission(request, obj):
            raise PermissionDenied
        try:
            fh = obj.resume.open('rb')
        except FileNotFoundError:
            raise Http404('Resume file missing')
        ext = Path(obj.resume.name).suffix
        filename = f'{slugify(obj.full_name) or "applicant"}-resume{ext}'
        return FileResponse(fh, as_attachment=True, filename=filename)

    @admin.display(description='Resume')
    def resume_link(self, obj):
        if obj.pk and obj.resume:
            url = reverse('admin:jobs_application_resume', args=[obj.pk])
            return format_html('<a href="{}">Download resume</a>', url)
        return '-'

    @admin.action(description='Export selected to CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="applications.csv"'
        writer = csv.writer(response)
        writer.writerow(['Job', 'Name', 'Email', 'Phone', 'Status', 'Applied at'])
        for a in queryset.select_related('job'):
            writer.writerow([
                _safe(a.job.title), _safe(a.full_name), _safe(a.email), _safe(a.phone),
                a.get_status_display(),
                timezone.localtime(a.applied_at).strftime('%Y-%m-%d %H:%M'),
            ])
        return response