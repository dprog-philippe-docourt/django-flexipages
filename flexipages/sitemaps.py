from django.apps import apps as django_apps
from django.contrib.sitemaps import Sitemap
from django.core.exceptions import ImproperlyConfigured

from flexipages.utils import get_site_config


class FlexiPagesSitemap(Sitemap):
    def __init__(self):
        self.current_site = None
        self.path_prefix = None

    def items(self):
        if not django_apps.is_installed('django.contrib.sites'):
            raise ImproperlyConfigured("FlexiPages requires django.contrib.sites, which isn't installed.")
        Site = django_apps.get_model('sites.Site')
        current_site = Site.objects.get_current()
        if current_site != self.current_site:
            self.current_site = current_site
            self.path_prefix = None
        return self.current_site.page_set.filter(registration_required=False)

    def location(self, obj):
        if self.path_prefix is None:
            self.path_prefix = ''
            if self.current_site is not None:
                current_config = get_site_config(self.current_site)
                if current_config:
                    self.path_prefix = current_config.path_prefix
        # Build dynamic absolute URL with proper path prefix.
        return self.path_prefix + obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.last_updated
