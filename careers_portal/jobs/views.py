from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ApplicationForm
from .models import Job


def home(request):
    jobs = Job.objects.open().select_related('department')[:6]
    return render(request, 'home.html', {'jobs': jobs})


def job_list(request):
    q = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()
    department = request.GET.get('department', '').strip()
    job_type = request.GET.get('job_type', '').strip()

    jobs = Job.objects.open().select_related('department')
    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if department:
        jobs = jobs.filter(department__name__icontains=department)
    if job_type in Job.JobType.values:
        jobs = jobs.filter(job_type=job_type)

    page_obj = Paginator(jobs, 10).get_page(request.GET.get('page'))
    return render(request, 'job_list.html', {
        'page_obj': page_obj,
        'search_query': q,
        'location': location,
        'department': department,
        'job_type': job_type,
        'job_types': Job.JobType.choices,
    })


def job_detail(request, slug):
    job = get_object_or_404(Job.objects.open(), slug=slug)
    return render(request, 'job_detail.html', {'job': job})


def apply_job(request, slug):
    job = get_object_or_404(Job.objects.open(), slug=slug)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES, job=job)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            try:
                application.save()
            except IntegrityError:
                form.add_error('email', 'You have already applied for this position with this email.')
            else:
                return redirect('thank_you', slug=job.slug)
    else:
        form = ApplicationForm(job=job)
    return render(request, 'apply_job.html', {'job': job, 'form': form})


def thank_you(request, slug):
    job = get_object_or_404(Job, slug=slug)
    return render(request, 'thank_you.html', {'job': job})
