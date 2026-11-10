
import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Job, Application


# Application Inline
class ApplicationInline(admin.TabularInline):
    model = Application
    extra = 0
    can_delete = False

    fields = (
        'full_name',
        'email',
        'phone',
        'status',
        'applied_at',
    )

    readonly_fields = (
        'full_name',
        'email',
        'phone',
        'status',
        'applied_at',
    )


# Job Admin
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'department',
        'location',
        'job_type',
        'is_active',
        'closing_date',
    )

    list_filter = (
        'job_type',
        'location',
        'is_active',
    )

    search_fields = (
        'title',
        'department',
        'location',
    )

    prepopulated_fields = {
        'slug': ('title',)
    }

    actions = [
        'close_selected_jobs',
        'reopen_selected_jobs',
    ]

    inlines = [ApplicationInline]

    @admin.action(description='Close selected jobs')
    def close_selected_jobs(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='Reopen selected jobs')
    def reopen_selected_jobs(self, request, queryset):
        queryset.update(is_active=True)


# Application Admin
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):

    list_display = (
        'full_name',
        'email',
        'job',
        'status',
        'applied_at',
        'download_resume',
    )

    list_filter = (
        'job',
        'status',
    )

    search_fields = (
        'full_name',
        'email',
        'phone',
    )

    readonly_fields = (
        'job',
        'full_name',
        'email',
        'phone',
        'resume',
        'cover_letter',
        'portfolio_url',
        'applied_at',
    )

    actions = ['export_selected_to_csv']

    @admin.display(description='Download Resume')
    def download_resume(self, obj):
        if obj.resume:
            return format_html(
                '<a href="{}" target="_blank">Download Resume</a>',
                obj.resume.url
            )
        return 'No Resume'

    @admin.action(description='Export selected applications to CSV')
    def export_selected_to_csv(self, request, queryset):

        response = HttpResponse(
            content_type='text/csv'
        )

        response['Content-Disposition'] = (
            'attachment; filename="applications.csv"'
        )

        writer = csv.writer(response)

        writer.writerow([
            'Full Name',
            'Email',
            'Phone',
            'Job',
            'Status',
            'Applied At',
        ])

        for application in queryset:
            writer.writerow([
                application.full_name,
                application.email,
                application.phone,
                application.job.title,
                application.status,
                application.applied_at,
            ])

        return response


# Custom Admin Branding
admin.site.site_header = "Avalanche High-Tech Enterprises"
admin.site.site_title = "Company HR Panel"
admin.site.index_title = "HR Management Dashboard"

