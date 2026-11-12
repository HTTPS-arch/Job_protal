import csv

from django.contrib import admin, messages
from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html

from .models import Application, Department, Job

# Custom title / header
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
    list_display = ('title', 'department', 'location', 'job_type',
                    'closing_date', 'is_active', 'application_count')
    list_filter = ('job_type', 'location', 'is_active')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ApplicationInline]
    actions = ['close_jobs', 'reopen_jobs']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(app_count=Count('applications'))

    @admin.display(description='Applications', ordering='app_count')
    def application_count(self, obj):
        return obj.app_count

    @admin.action(description='Close selected jobs')
    def close_jobs(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, f'{n} job(s) closed.', messages.SUCCESS)

    @admin.action(description='Reopen selected jobs')
    def reopen_jobs(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f'{n} job(s) reopened.', messages.SUCCESS)


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

    @admin.display(description='Resume')
    def resume_link(self, obj):
        if obj.resume:
            return format_html('<a href="{}" target="_blank">Download resume</a>', obj.resume.url)
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