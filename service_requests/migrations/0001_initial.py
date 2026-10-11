import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemState',
            fields=[
                ('key', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('value', models.TextField()),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'system_state',
            },
        ),
        migrations.CreateModel(
            name='ServiceRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=150)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('IT', 'IT'), ('MAINTENANCE', 'Maintenance'), ('GENERAL', 'General')], max_length=20)),
                ('priority', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')], default='MEDIUM', max_length=10)),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'), ('RESOLVED', 'Resolved')], default='OPEN', max_length=20)),
                ('status_changed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('overdue', models.BooleanField(default=False)),
                ('overdue_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'service_requests',
                'permissions': [('read_requests', 'Can read service requests'), ('create_requests', 'Can create service requests'), ('update_requests', 'Can edit service requests'), ('delete_requests', 'Can delete service requests'), ('update_request_status', "Can change a request's status"), ('read_dashboard', 'Can read the dashboard summary')],
                'default_permissions': (),
                'indexes': [models.Index(fields=['status'], name='sr_status_idx'), models.Index(fields=['priority'], name='sr_priority_idx'), models.Index(fields=['-created_at'], name='sr_created_at_idx'), models.Index(condition=models.Q(('overdue', False), ('status__in', ['OPEN', 'IN_PROGRESS'])), fields=['status_changed_at'], name='sr_overdue_candidates_idx'), models.Index(condition=models.Q(('overdue', True)), fields=['-created_at'], name='sr_overdue_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(('category__in', ['IT', 'MAINTENANCE', 'GENERAL'])), name='sr_category_chk'), models.CheckConstraint(condition=models.Q(('priority__in', ['LOW', 'MEDIUM', 'HIGH'])), name='sr_priority_chk'), models.CheckConstraint(condition=models.Q(('status__in', ['OPEN', 'IN_PROGRESS', 'RESOLVED'])), name='sr_status_chk')],
            },
        ),
    ]
