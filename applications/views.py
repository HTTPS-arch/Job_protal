
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from jobs.models import Job
from .forms import ApplicationForm


def apply_for_job(request, slug):
    job = get_object_or_404(
        Job,
        slug=slug,
        is_active=True
    )

    if request.method == 'POST':
        form = ApplicationForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.save()

            messages.success(
                request,
                'Your application has been submitted successfully!'
            )

            return redirect('job_list')

    else:
        form = ApplicationForm()

    return render(request, 'applications/apply.html', {
        'form': form,
        'job': job
    })
