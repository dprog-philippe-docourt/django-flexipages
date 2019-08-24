from dbtemplates import models as dbtemplates_models
from dbtemplates.utils.cache import remove_cached_template
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.template import engines
from django.template.defaultfilters import striptags, truncatewords_html
from django.urls import get_script_prefix
from django.utils import timezone
from django.utils.encoding import iri_to_uri
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ugettext

from stringrenderer import StringTemplateRenderer, check_template_syntax
from flexipages.cache import delete_cache_for_page
from flexipages.constants import EDITION_CONTEXT_ATTRIBUTE_NAME, PAGE_CACHE_DURATIONS

PAGE_CACHE_DURATIONS_CHOICES = (
    (PAGE_CACHE_DURATIONS.none, _("no caching")),
    (PAGE_CACHE_DURATIONS.one_minute, _("1 minute")),
    (PAGE_CACHE_DURATIONS.five_minutes, _("5 minutes")),
    (PAGE_CACHE_DURATIONS.fifteen_minutes, _("15 minutes")),
    (PAGE_CACHE_DURATIONS.thirty_minutes, _("30 minutes")),
    (PAGE_CACHE_DURATIONS.one_hour, _("1 hour")),
    (PAGE_CACHE_DURATIONS.three_hours, _("3 hours")),
    (PAGE_CACHE_DURATIONS.six_hours, _("6 hours")),
    (PAGE_CACHE_DURATIONS.twelve_hours, _("12 hours")),
    (PAGE_CACHE_DURATIONS.one_day, _("1 day")),
    (PAGE_CACHE_DURATIONS.three_days, _("3 days")),
    (PAGE_CACHE_DURATIONS.one_week, _("1 week")),
    (PAGE_CACHE_DURATIONS.two_weeks, _("2 weeks")),
    (PAGE_CACHE_DURATIONS.one_month, _("1 month")),
)


class PageTemplate(dbtemplates_models.Template):
    verbose_name = _('page template')
    verbose_name_plural = _('page templates')

    def clean(self):
        super().clean()
        valid, error = check_template_syntax(self.content)
        if not valid:
            raise ValidationError(
                '%s %s %s' % (
                    ugettext("The given template is not valid."),
                    error,
                    ugettext("Please correct the syntax of this template.")
                ))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Invalidate cache.
        remove_cached_template(self)
        # Any page using this template is considered as updated.
        # NB: in case of interconnected templates via extend and include directives, the pages are not refreshed.
        Page.objects.filter(template=self).update(last_updated=timezone.now())

    class Meta:
        proxy = True


class PageManager(models.Manager):
    def get_pages_for_request(self, request):
        current_site = get_current_site(request)
        pages = self.filter(sites=current_site)
        if not request.user.is_authenticated:
            pages = pages.filter(registration_required=False)
        return pages


class TagManager(models.Manager):
    def get_tags_related_to_page(self, page, is_editing=False):
        return self.filter(pageitem__in=PageItem.objects.get_items_for_page(page=page, is_editing=is_editing)).distinct()


class Tag(models.Model):
    objects = TagManager()
    name = models.CharField(_('name'), max_length=64, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']


class Page(models.Model):
    objects = PageManager()
    path = models.CharField(_('path'), max_length=100, db_index=True, help_text=_('The path of the URL to access this page.'))
    title = models.CharField(_('title'), max_length=256)
    template = models.ForeignKey(PageTemplate, on_delete=models.PROTECT, verbose_name=_('template'), help_text=_('The template used to render the page.'))
    sites = models.ManyToManyField(Site, verbose_name=_('sites'), help_text=_("The sites on which the URL of this page must be available."))
    registration_required = models.BooleanField(_('registration required'), help_text=_("If this is checked, only logged-in users will be able to view the page."), default=False,)
    cache_timeout = models.PositiveSmallIntegerField(_('page cache timeout'), default=PAGE_CACHE_DURATIONS.one_hour, choices=PAGE_CACHE_DURATIONS_CHOICES, help_text=_("Indicates for how long the page is cached on the server side."))
    enable_client_side_caching = models.BooleanField(_('enable client side caching'), default=True, help_text=_("Tells whether the client's browser is allowed to keep this page in cache. When enabled, the user needs to fully refresh the page in his web browser for obtaining the latest version."))
    description = models.CharField(_('description'), blank=True, max_length=256, help_text=_('A description of this page.'))
    tags = models.ManyToManyField(Tag, verbose_name=_('tags'), blank=True)
    priority = models.PositiveSmallIntegerField(_('priority'), default=0, null=True, blank=True, help_text=_("The page priority for navigation. Lowest priority comes first. A blank field means that the page should not appears in navigation bars."))
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='+', verbose_name=_('parent'), null=True, default=None, editable=False)
    level = models.PositiveSmallIntegerField(_('level'), default=0, editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True, editable=False)
    last_updated = models.DateTimeField(db_index=True, auto_now=True, editable=False)

    def __str__(self):
        return "%s -- %s" % (self.path, self.title)

    def save(self, *args, **kwargs):
        # Adjust page level according to path.
        self.level = self.path.strip('/').count('/')
        self.parent = self.search_parent_from_path(self.level, self.path)
        super().save(*args, **kwargs)
        # Invalidate cache.
        delete_cache_for_page(self)

    def get_absolute_url(self):
        """
        The page model has no knowledge of the site configuration it depends on since it may vary from one request to
        another. Therefore, the absolute URL is not really absolute, and has to be determined dynamically for each
        request.
        """
        # Handle script prefix manually because we bypass reverse()
        script_prefix = get_script_prefix()
        absolute_path = iri_to_uri(script_prefix.rstrip('/') + self.path)
        return absolute_path

    def get_siblings_for_navigation(self):
        return Page.objects.filter(parent_id=self.parent_id).exclude(priority__isnull=True)

    def get_children_for_navigation(self):
        return Page.objects.filter(parent=self).exclude(priority__isnull=True)

    @staticmethod
    def search_parent_from_path(level, page_path):
        if not page_path or page_path == '/':
            return None
        parent_path = '/'.join(page_path.rstrip('/').split('/')[:-1])
        # Use level combined with 'path__startswith' to be insensitive to trailing slashes that might not be consistent.
        parent = Page.objects.filter(level=level - 1, path__startswith=parent_path).first()
        # Handle possible empty level. E. g.: in '/products' <- '/product/flexipages/detail' there could be no
        # intermediate page for the '/products/flexipages' level.
        if not parent and parent_path:
            return Page.search_parent_from_path(level=level - 1, path=parent_path)
        return parent

    def get_parent_for_navigation(self):
        if self.parent and self.parent.priority is None:
            # Recurse in case of hidden page in navigation structure.
            return self.parent.get_parent_page()
        return self.parent

    def get_page_timeout_in_seconds(self):
        if self.cache_timeout == PAGE_CACHE_DURATIONS.none:
            return 0
        if self.cache_timeout == PAGE_CACHE_DURATIONS.one_minute:
            return 60
        if self.cache_timeout == PAGE_CACHE_DURATIONS.five_minutes:
            return 300
        if self.cache_timeout == PAGE_CACHE_DURATIONS.fifteen_minutes:
            return 900
        if self.cache_timeout == PAGE_CACHE_DURATIONS.thirty_minutes:
            return 1800
        if self.cache_timeout == PAGE_CACHE_DURATIONS.one_hour:
            return 3600
        if self.cache_timeout == PAGE_CACHE_DURATIONS.three_hours:
            return 3600 * 3
        if self.cache_timeout == PAGE_CACHE_DURATIONS.six_hours:
            return 3600 * 6
        if self.cache_timeout == PAGE_CACHE_DURATIONS.twelve_hours:
            return 3600 * 12
        if self.cache_timeout == PAGE_CACHE_DURATIONS.one_day:
            return 3600 * 24
        if self.cache_timeout == PAGE_CACHE_DURATIONS.three_days:
            return 3600 * 24 * 3
        if self.cache_timeout == PAGE_CACHE_DURATIONS.one_week:
            return 3600 * 24 * 7
        if self.cache_timeout == PAGE_CACHE_DURATIONS.one_month:
            return 3600 * 24 * 30
        raise ValueError(_("Unrecognized timeout duration."))

    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        ordering = ('level', 'priority', 'path')


class PageItemQuerySet(models.QuerySet):
    def get_items_for_page(self, page, is_editing=False):
        items = self.filter(pageitemlayout__page=page)
        if not is_editing:
            items = items.get_published_items()
        return items

    def get_published_items(self):
        today = timezone.now().date()
        return self.filter(Q(publishing_end_date__isnull=True) | Q(publishing_end_date__gte=today)).filter(Q(publishing_start_date__isnull=False) | Q(publishing_start_date__lte=today))


class PageItemManager(models.Manager):
    def get_queryset(self):
        return PageItemQuerySet(self.model, using=self._db)  # Important!

    def get_items_for_page(self, page, is_editing=False):
        return self.get_queryset().get_items_for_page(page=page, is_editing=is_editing)

    def get_published_items(self):
        return self.get_queryset().get_published_items()


class PageItem(models.Model):
    objects = PageItemManager()
    content = models.TextField(null=False, blank=False, editable=True, verbose_name=_('content'), max_length=1e6, help_text=_("The content of this item."))
    description = models.CharField(_('description'), max_length=256, blank=True, help_text=_("Short description of this content"))
    title = models.CharField(null=False, default='', blank=True, editable=True, verbose_name=_('title'), max_length=128, help_text=_("An optional title for this content."))
    tags = models.ManyToManyField(Tag, verbose_name=_('tags'), blank=True)
    publishing_start_date = models.DateField(_('publishing start date'), default=None, blank=True, null=True, help_text=_("Indicates when this item must be published. A blank field means that this content is unpublished and therefore not displayed anywhere."))
    publishing_end_date = models.DateField(_('publishing end date'), default=None, blank=True, null=True, help_text=_("Indicates when the publication of this content should be over. A blank field means that this content will by available forever."))
    render_content_as_template = models.BooleanField(_('render content as template'), default=False, help_text=_("Indicates whether the content is interpreted and rendered as a Django template. The content is interpreted as raw HTML when disabled."))
    use_wysiwyg_editor = models.BooleanField(_('use WYSIWYG editor'), default=True, help_text=_("Indicates whether the content should be rendered with a WYSIWYG editor for HTML."))
    author = models.ForeignKey(User, verbose_name=_('author'), related_name='authors_items', null=True, on_delete=models.SET_NULL, blank=True, help_text=_("The author of this item."))
    last_edited_by = models.ForeignKey(User, verbose_name=_('last edited by'), related_name='edited_items', null=True, on_delete=models.SET_NULL, blank=True, help_text=_("The edited items of the author."))
    created = models.DateTimeField(auto_now_add=True, db_index=True, editable=False)
    last_updated = models.DateTimeField(db_index=True, auto_now=True, editable=False)

    def __str__(self):
        return (self.title or self.description) or '%s %i' % (self._meta.verbose_name, self.pk)

    def clean(self):
        if self.render_content_as_template:
            valid, error = check_template_syntax(self.content)
            if not valid:
                raise ValidationError(
                    '%s %s %s' % (
                        ugettext("The given content cannot be interpreted and rendered as a template."),
                        error,
                        ugettext("Please correct the syntax or deactivate the option for rendering the content as a template.")
                    ))

    def save(self, *args, **kwargs):
        if not self.description:
            # Extract the first few words of the content and remove the html tags.
            self.description = striptags(truncatewords_html(self.content, 15))[:257]
        if hasattr(self, '_renderer'):
            delattr(self, '_renderer')
        if not self.author:
            self.author = self.last_edited_by
        super().save(*args, **kwargs)

        # Sync last update of pages showing this item.
        related_pages = Page.objects.filter(id__in=self.pageitemlayout_set.values_list('page_id', flat=True))
        related_pages.update(last_updated=timezone.now())

        # Invalidate cache.
        for page in related_pages:
            delete_cache_for_page(page)

    def render(self):
        if self.render_content_as_template:
            # Build renderer if needed.
            if not hasattr(self, '_renderer'):
                setattr(self, '_renderer', StringTemplateRenderer(self.content, extra_tags=['flexipages']))
            rendered_content = self._renderer.render_template(context=dict(item=self))
        else:
            # Rendered content is equal to content when no template is given.
            rendered_content = self.content
        rendered_content = '<a id="item_%s"></a>%s' % (self.pk, rendered_content)
        rendered_content = mark_safe(rendered_content)
        edition_context = getattr(self, EDITION_CONTEXT_ATTRIBUTE_NAME, None)
        if edition_context:
            django_engine = engines['django']
            template = django_engine.get_template('flexipages/edition/item_toolbar.html')
            rendered_content = template.render(context=dict(edition_context=edition_context, item=self, rendered_content=rendered_content))
        return rendered_content

    @property
    def tag_names(self):
        return self.tags.values_list('name', flat=True)

    @property
    def is_not_published_yet(self):
        return self.publishing_start_date is None or self.publishing_start_date > timezone.now().date()

    @property
    def is_no_longer_published(self):
        return self.publishing_end_date is not None and self.publishing_end_date < timezone.now().date()

    class Meta:
        verbose_name = _('page item')
        verbose_name_plural = _('page items')


class PageItemLayout(models.Model):
    item = models.ForeignKey(PageItem, on_delete=models.CASCADE, verbose_name=_('item'), help_text=_("The item that we want to locate on the given page."))
    page = models.ForeignKey(Page, on_delete=models.CASCADE, verbose_name=_('page'), help_text=_("The page where the item must be displayed."))
    priority = models.SmallIntegerField(_('priority'), default=None, blank=True, null=True, help_text=_("The priority for the selected item on the given page, and the given zone if defined. Lowest priority comes first. An empty field implies that items are sorted by reversed chronological order of items creation."))
    zone_name = models.SlugField(_('zone name'), default='', blank=True, help_text=_("The name of the page area that this item belongs to."))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Sync last update of page showing the item from this layout.
        self.page.last_updated = timezone.now()
        self.page.save(update_fields=['last_updated'])

    def __str__(self):
        return '%s, %s' % (self.page, self.item)

    class Meta:
        verbose_name = _('page item layout')
        verbose_name_plural = _('page item layouts')
        unique_together = ('page', 'item')
        ordering = ['page', 'zone_name', 'priority', '-item__created']


def validate_path_prefix(value):
    if value != '':
        if not value.startswith('/'):
            raise ValidationError(_("The path prefix must start with a '/'."))
        if value.endswith('/'):
            raise ValidationError(_("The path prefix must not end with a '/'."))


class SiteConfiguration(models.Model):
    site = models.OneToOneField(Site, on_delete=models.CASCADE, verbose_name=_('site'), help_text=_("The site to configure."))
    path_prefix = models.CharField(_('path prefix'), max_length=128, default='', blank=True, validators=[validate_path_prefix], help_text=_("The default path prefix for serving the pages. All pages will be served relative to this prefix. For instance a page with path '/home' will be served under '/cms/home' if the prefix is set to '/cms'."))
    search_results_template = models.ForeignKey(PageTemplate, on_delete=models.PROTECT, verbose_name=_('search results template'), help_text=_("The template used for displaying search results."))

    def __str__(self):
        return '%s for %s' % (self._meta.verbose_name, self.site)

    class Meta:
        verbose_name = _('site configuration')
        verbose_name_plural = _('sites configuration')
        ordering = ['site__name']
