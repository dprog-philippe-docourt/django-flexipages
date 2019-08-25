from os import path
from os.path import dirname
from typing import Mapping

from django.apps import apps as django_apps
from django.contrib.sites.shortcuts import get_current_site
from django.template import engines
from django.template.defaultfilters import truncatewords
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from flexipages.constants import FLEXIPAGES_EDITOR_GROUP_NAME, FLEXIPAGES_ADMIN_GROUP_NAME, FLEXIPAGES_SITE_DESIGNER_GROUP_NAME, \
    SEMANTIC_UI_CSS_URL, IS_EDITING_ATTRIBUTE_NAME


def setup_default_templates(model, force_update):
    app_name = 'flexipages'
    relative_dir = path.join('templates', app_name, 'defaults')
    base_dir = path.join(dirname(__file__), relative_dir)
    manager = model.objects

    def setup_from_file(file_path):
        with open(file_path, mode='rt', encoding='utf-8') as f:
            content = f.read()
            template_name = app_name + file_path[len(base_dir):]
            if force_update:
                manager.update_or_create(name=template_name, defaults=dict(content=content))
            else:
                manager.get_or_create(name=template_name, defaults=dict(content=content))

    setup_from_file(path.join(base_dir, 'pages', 'base.html'))
    setup_from_file(path.join(base_dir, 'pages', 'search_results.html'))
    setup_from_file(path.join(base_dir, 'components', 'tags_related_to_page.html'))
    setup_from_file(path.join(base_dir, 'components', 'item_tags.html'))
    setup_from_file(path.join(base_dir, 'components', 'search_form.html'))
    setup_from_file(path.join(base_dir, 'menus', 'breadcrumbs.html'))


def get_default_base_template_for_page(page_template_model):
    try:
        return page_template_model.objects.get(name='flexipages/pages/base.html')
    except (page_template_model.DoesNotExist, page_template_model.MultipleObjectsReturned):
        pass


def get_site_config(site):
    SiteConfiguration = django_apps.get_model('flexipages.SiteConfiguration')
    try:
        return SiteConfiguration.objects.get(site=site)
    except SiteConfiguration.DoesNotExist:
        pass


def get_current_site_and_config(request):
    current_site = get_current_site(request)
    return current_site, get_site_config(current_site)


def get_base_url_for_page(page, request):
    page_path = page.path.rstrip('/')
    request_path = request.path.rstrip('/')
    base_url = request_path[:-len(page_path)]
    return base_url


def get_permissions_for_user(user) -> Mapping[str, bool]:
    """Tells whether the currently authenticated user has permission to edit a page, its content and or its template."""
    if user.is_authenticated:
        is_admin = user.groups.filter(name=FLEXIPAGES_EDITOR_GROUP_NAME).exists()
        is_editor = user.groups.filter(name=FLEXIPAGES_EDITOR_GROUP_NAME).exists()
        is_designer = user.groups.filter(name=FLEXIPAGES_SITE_DESIGNER_GROUP_NAME).exists()
        return dict(
            can_edit_content=user.is_superuser or is_admin or is_designer or is_editor,
            can_edit_template=user.is_superuser or is_designer,
            can_edit_page=user.is_superuser or is_admin
        )
    return dict(
            can_edit_content=False,
            can_edit_template=False,
            can_edit_page=False
        )
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name__in=(FLEXIPAGES_EDITOR_GROUP_NAME, FLEXIPAGES_ADMIN_GROUP_NAME, FLEXIPAGES_SITE_DESIGNER_GROUP_NAME)).exists())


def patch_response_for_inline_editing(request, page, edition_context: Mapping[str, bool], response_to_patch):
    django_engine = engines['django']
    rendered_content = response_to_patch.rendered_content
    if edition_context['is_editing']:
        page_header_template = django_engine.get_template('flexipages/edition/header_extra.html')
        # Once for all editable items, insert the link to CSS.
        context = dict(SEMANTIC_UI_CSS_URL=SEMANTIC_UI_CSS_URL)
        header_extra = page_header_template.render(request=request, context=context)
        # Patch header.
        rendered_content = rendered_content.replace('</head>', "%s</head>" % header_extra)
    page_edit_template = django_engine.get_template('flexipages/edition/page_toolbar.html')
    context = dict(SEMANTIC_UI_CSS_URL=SEMANTIC_UI_CSS_URL, edition_context=edition_context, IS_EDITING_ATTRIBUTE_NAME=IS_EDITING_ATTRIBUTE_NAME, page=page)
    edition_toolbar = page_edit_template.render(request=request, context=context)
    # Insert page editing toolbar.
    rendered_content = rendered_content.replace('</body>', "%s</body>" % edition_toolbar)
    # Set the patched content of the response
    response_to_patch.content = mark_safe(rendered_content)


def get_formatted_match(text: str, to_search: str):
    try:
        match_start = text.lower().index(to_search.lower())
    except ValueError:
        return None
    matched_length = len(to_search)
    context_length = 40
    before = text[match_start - context_length:match_start]
    matched_text = text[match_start:match_start + matched_length]
    after = text[match_start + matched_length:match_start + matched_length + context_length]
    after = (after[0] if after[0].isspace() else '') + truncatewords(after, context_length // 6)
    match = format_html('{}<span class="content-match">{}</span>{}', before, matched_text, after)
    return match
