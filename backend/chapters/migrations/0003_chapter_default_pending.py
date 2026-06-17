"""Default a newly created chapter to `pending` (in the review queue) rather than
`unverified`. A fresh chapter is an application awaiting review; `unverified` is
reserved for one that was reviewed and not approved. Existing rows are untouched.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chapters", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chapter",
            name="verification_status",
            field=models.CharField(
                choices=[
                    ("unverified", "Unverified"),
                    ("pending", "Pending"),
                    ("verified", "Verified"),
                    ("suspended", "Suspended"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
