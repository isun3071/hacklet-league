"""Replace the default Sites-framework record (example.com) with HackLet League.

django-allauth renders `{{ site_name }}` / `{{ site_domain }}` from the current
Site into every transactional email (signup, verification, password reset).
Without this, those emails read "Hello from example.com!". Run as data so a
fresh database (dev, a new Hetzner host) comes up correct without a manual step.
"""
from django.conf import settings
from django.db import migrations

DOMAIN = "hackletleague.com"
NAME = "HackLet League"


def set_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={"domain": DOMAIN, "name": NAME},
    )


def reset_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={"domain": "example.com", "name": "example.com"},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("sites", "0002_alter_domain_unique"),
    ]
    operations = [migrations.RunPython(set_site, reset_site)]
