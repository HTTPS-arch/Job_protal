import django.core.validators
from django.db import migrations, models

def populate_job_metadata(apps, schema_editor):
    Job = apps.get_model('jobs', 'Job')
    db_alias = schema_editor.connection.alias

    jobs = Job.objects.using(db_alias).all().only(
        'id', 'created_at', 'date_posted', 'job_code'
    )

    for job in jobs.iterator():
        updates = {}

        if not job.job_code:
            updates['job_code'] = f'JOB-{1000 + job.id}'

        if not job.date_posted and job.created_at:
            updates['date_posted'] = job.created_at.date()

        if updates:
            Job.objects.using(db_alias).filter(id=job.id).update(**updates)

class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_storedfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='job',
            name='country',
            field=models.CharField(blank=True, default='IN', help_text='ISO country code, e.g. IN', max_length=2),
        ),
        migrations.AddField(
            model_name='job',
            name='date_posted',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='direct_apply',
            field=models.BooleanField(default=True, editable=False),
        ),
        migrations.AddField(
            model_name='job',
            name='is_expired',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='job',
            name='is_remote',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='job',
            name='job_code',
            field=models.CharField(blank=True,null=True,max_length=20,unique=True
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='postal_code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='job',
            name='salary_currency',
            field=models.CharField(blank=True, default='INR', max_length=3),
        ),
        migrations.AddField(
            model_name='job',
            name='salary_max',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='salary_min',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='salary_period',
            field=models.CharField(blank=True, choices=[('HOUR', 'Per Hour'), ('DAY', 'Per Day'), ('WEEK', 'Per Week'), ('MONTH', 'Per Month'), ('YEAR', 'Per Year')], max_length=10),
        ),
        migrations.AddField(
            model_name='job',
            name='state',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='job',
            name='street_address',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RunPython(
            populate_job_metadata,
            migrations.RunPython.noop,
        ),

        migrations.AlterField(
            model_name='job',
            name='job_code',
            field=models.CharField(
                blank=True,
                max_length=20,
                unique=True
            ),
        ),
        migrations.AlterField(
            model_name='application',
            name='phone',
            field=models.CharField(max_length=20, validators=[django.core.validators.RegexValidator(message='Enter a valid phone number (10-15 digits, optional +).', regex='^\\+?[0-9\\-]{10,15}$')]),
        ),
    ]
