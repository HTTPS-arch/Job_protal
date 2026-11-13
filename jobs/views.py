
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Job


def job_list(request):
    jobs_list = Job.objects.filter(
        is_active=True,
        closing_date__gte=timezone.localdate()
    ).order_by('-created_at')

    paginator = Paginator(jobs_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'jobs': page_obj,
        'page_obj': page_obj,
    }

    return render(request, 'jobs/home.html', context)


def job_detail(request, slug):
    job = get_object_or_404(
        Job,
        slug=slug,
        is_active=True,
        closing_date__gte=timezone.localdate()
    )

    return render(request, 'jobs/job_detail.html', {
        'job': job
    })
