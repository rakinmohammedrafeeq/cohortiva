# Generated manually for security remediation

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0003_profile_email_verification_sent_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='password_changed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
