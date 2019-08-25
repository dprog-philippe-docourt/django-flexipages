from django import apps as global_apps
from django.db import router, DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate
from django.utils import timezone

from flexipages.constants import FLEXIPAGES_EDITOR_GROUP_NAME, FLEXIPAGES_ADMIN_GROUP_NAME, \
    FLEXIPAGES_SITE_DESIGNER_GROUP_NAME, CONTENT_RENDERING_MODE
from flexipages.utils import setup_default_templates, get_default_base_template_for_page


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
        Group = apps.get_model('auth', 'Group')
    except LookupError:
        return
    if not router.allow_migrate_model(using, Group):
        return
    Group.objects.get_or_create(name=FLEXIPAGES_EDITOR_GROUP_NAME)
    Group.objects.get_or_create(name=FLEXIPAGES_ADMIN_GROUP_NAME)
    Group.objects.get_or_create(name=FLEXIPAGES_SITE_DESIGNER_GROUP_NAME)


def create_flexipages_default_root_page(verbosity, using=DEFAULT_DB_ALIAS, apps=global_apps, **kwargs):
    try:
        Page = apps.get_model('flexipages', 'Page')
        PageItem = apps.get_model('flexipages', 'PageItem')
        PageItemLayout = apps.get_model('flexipages', 'PageItemLayout')
        PageTemplate = apps.get_model('flexipages', 'PageTemplate')
        Site = apps.get_model('sites', 'Site')
    except LookupError:
        return
    if not (router.allow_migrate_model(using, Page) and router.allow_migrate_model(using, PageItem) and router.allow_migrate_model(using, PageItemLayout) and router.allow_migrate_model(using, PageTemplate)):
        return
    template = get_default_base_template_for_page(PageTemplate)
    page, created = Page.objects.get_or_create(path='/', defaults=dict(template=template, priority=0, title='Home'))
    if created:
        default_site = Site.objects.first()
        page.sites.add(default_site)
        content = """<h2>Welcome to FlexiPages!</h2>
        <p>This is the default root page generated when applying migrations for django-flexipages for the first time.</p>
        <p>Click the button <em>Activate editing mode</em> at the bottom right of the page to start editing this page this page.</p>"""
        today = timezone.now().date()
        page_item = PageItem.objects.create(publishing_start_date=today, content=content)
        PageItemLayout.objects.create(page=page, item=page_item, priority=0)
        page_item = PageItem.objects.create(publishing_start_date=today,
                                            content="""<h2>Example of Page Item</h2><p>{% lorem %}</p>""", content_rendering_mode=CONTENT_RENDERING_MODE.django_template, use_wysiwyg_editor=False)
        PageItemLayout.objects.create(page=page, item=page_item, priority=100)


class FlexiPagesConfig(global_apps.AppConfig):
    name = 'flexipages'
    verbose_name = "FlexiPages"

    def ready(self):
        post_migrate.connect(create_default_templates, sender=self)
        post_migrate.connect(create_flexipages_admin_groups, sender=self)
        post_migrate.connect(create_flexipages_default_root_page, sender=self)

        # @debug
        # from django.conf import settings
        # if settings.DEBUG:
        #     from flexipages.models import PageTemplate
        #     setup_default_templates(PageTemplate, force_update=True)
