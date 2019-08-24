from django import apps as global_apps
from django.db import router, DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate

from flexipages.constants import FLEXIPAGES_EDITOR_GROUP_NAME, FLEXIPAGES_ADMIN_GROUP_NAME, FLEXIPAGES_SITE_DESIGNER_GROUP_NAME
from flexipages.utils import setup_default_templates


def create_default_templates(verbosity, using=DEFAULT_DB_ALIAS, apps=global_apps, **kwargs):
    try:
        PageTemplate = apps.get_model('flexipages', 'PageTemplate')
    except LookupError:
        return

    if not router.allow_migrate_model(using, PageTemplate):
        return

    setup_default_templates(PageTemplate, force_update=False)


def create_flexipages_admin_groups(verbosity, using=DEFAULT_DB_ALIAS, apps=global_apps, **kwargs):
    try:
        Group = apps.get_model('django.contrib.auth', 'Group')
    except LookupError:
        return
    if not router.allow_migrate_model(using, Group):
        return
    Group.objects.get_or_create(name=FLEXIPAGES_EDITOR_GROUP_NAME)
    Group.objects.get_or_create(name=FLEXIPAGES_ADMIN_GROUP_NAME)
    Group.objects.get_or_create(name=FLEXIPAGES_SITE_DESIGNER_GROUP_NAME)


class FlexiPagesConfig(global_apps.AppConfig):
    name = 'flexipages'
    verbose_name = "FlexiPages"

    def ready(self):
        # @debug
        # from django.conf import settings
        # if settings.DEBUG:
        #     from flexipages.models import PageTemplate
        #     setup_default_templates(PageTemplate, force_update=True)
        post_migrate.connect(create_default_templates, sender=self)
        post_migrate.connect(create_flexipages_admin_groups, sender=self)
