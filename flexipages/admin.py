from dbtemplates import admin as dbtemplates_admin
import djangocodemirror
from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from djangocodemirror.widgets import CodeMirrorAdminWidget

from flexipages.models import *


class PageTemplateAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget = djangocodemirror.widgets.CodeMirrorAdminWidget(config_name="django")
        self.fields['content'].required = True


class PageTemplateAdmin(dbtemplates_admin.TemplateAdmin):
    save_on_top = True
    form = PageTemplateAdminForm


class TagAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'name']
    list_editable = ['name']
    search_fields = ['name']


class ItemLayoutInline(admin.TabularInline):
    model = PageItemLayout
    extra = 1
    autocomplete_fields = ['item', 'page']


class PageAdmin(admin.ModelAdmin):
    save_on_top = True
    inlines = (ItemLayoutInline, )
    list_display = ['__str__', 'path', 'template', 'priority', 'registration_required', 'cache_timeout', 'enable_client_side_caching']
    list_editable = ['path', 'priority', 'registration_required', 'cache_timeout', 'enable_client_side_caching']
    search_fields = ['path']
    list_filter = ['template', 'sites', 'level', 'priority', 'registration_required', 'enable_client_side_caching']
    filter_horizontal = ['tags']
    list_select_related = ['template']

    readonly_fields = ['created', 'last_updated', 'parent', 'level']

    fieldsets = (
        (None, {
            'fields': (('path', 'title'), ('template', 'priority'), 'sites'),
        }),
        (_("Advanced"), {
            'fields': ('description', 'registration_required', ('cache_timeout', 'enable_client_side_caching'), 'tags'),
            'classes': ('collapse',),
        }),
        (_('Information'), {
            'fields': (('created', 'last_updated'), ('parent', 'level')),
            'classes': ('collapse',),
        }),
    )


class PageItemForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.use_wysiwyg_editor:
            self.fields['content'].widget = CKEditorWidget()
        elif self.instance.content_rendering_mode == CONTENT_RENDERING_MODE.html:
            self.fields['content'].widget = djangocodemirror.widgets.CodeMirrorAdminWidget(config_name="html")
        elif self.instance.content_rendering_mode == CONTENT_RENDERING_MODE.django_template:
            self.fields['content'].widget = djangocodemirror.widgets.CodeMirrorAdminWidget(config_name="django")
        elif self.instance.content_rendering_mode == CONTENT_RENDERING_MODE.markdown:
            self.fields['content'].widget = djangocodemirror.widgets.CodeMirrorAdminWidget(config_name="markdown")
        elif self.instance.content_rendering_mode == CONTENT_RENDERING_MODE.json:
            self.fields['content'].widget = djangocodemirror.widgets.CodeMirrorAdminWidget(config_name="json")
        elif self.instance.content_rendering_mode == CONTENT_RENDERING_MODE.javascript:
            self.fields['content'].widget = djangocodemirror.widgets.CodeMirrorAdminWidget(config_name="json")


class PageItemAdmin(admin.ModelAdmin):
    save_on_top = True
    inlines = (ItemLayoutInline,)
    form = PageItemForm
    list_display = ['__str__', 'title', 'publishing_start_date', 'publishing_end_date', 'content_rendering_mode']
    list_editable = ['title', 'publishing_start_date', 'publishing_end_date', 'content_rendering_mode']
    search_fields = ['content', 'title', 'tags__name']
    list_filter = ['tags', 'content_rendering_mode', 'use_wysiwyg_editor', ('author', admin.RelatedOnlyFieldListFilter), ('last_edited_by', admin.RelatedOnlyFieldListFilter)]
    date_hierarchy = 'created'
    readonly_fields = ['created', 'last_updated', 'last_edited_by']
    filter_horizontal = ['tags']
    fieldsets = (
        (_('Content, rendering and interpretation'), {
            'fields': (('content_rendering_mode', 'use_wysiwyg_editor'), 'content'),
        }),
        (_('Publishing'), {
            'fields': (('publishing_start_date', 'publishing_end_date'),),
        }),
        (_('Optional'), {
            'fields': (('title', 'description'), 'tags'),
            'classes': ('collapse',),
        }),
        (_('Modifications'), {
            'fields': ('author', ('last_edited_by', 'created', 'last_updated'),),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if form.changed_data:
            obj.last_edited_by = request.user
        super().save_model(request, obj, form, change)


class PageItemLayoutAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'priority', 'zone_name']
    list_editable = ['priority', 'zone_name']
    search_fields = ['page__path']
    list_filter = ['page', 'zone_name']
    list_select_related = ['page', 'item']
    autocomplete_fields = ['item', 'page']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['item'] + list(self.readonly_fields)
        return self.readonly_fields


class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'path_prefix', 'search_results_template']
    list_editable = ['path_prefix', 'search_results_template']
    search_fields = ['site__domain', 'site__name']
    list_select_related = ['site', 'search_results_template']
    autocomplete_fields = ['site']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['site'] + list(self.readonly_fields)
        return self.readonly_fields


admin.site.register(PageTemplate, PageTemplateAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(PageItem, PageItemAdmin)
admin.site.register(PageItemLayout, PageItemLayoutAdmin)
admin.site.register(SiteConfiguration, SiteConfigurationAdmin)
