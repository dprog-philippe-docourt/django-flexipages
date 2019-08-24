from typing import Mapping

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import striptags
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.cache import patch_cache_control
from django.utils.html import format_html
from django.utils.translation import ugettext
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST

from flexipages.cache import get_pages_cache, get_page_cache_key
from flexipages.constants import IS_EDITING_ATTRIBUTE_NAME, PAGE_CACHE_DURATIONS, SEARCH_RESULTS_PATH, \
    EDITION_CONTEXT_ATTRIBUTE_NAME
from flexipages.forms import SearchContentsForm
from flexipages.models import Page, PageItem, PageItemLayout, Tag
from flexipages.utils import get_current_site_and_config, get_base_url_for_page, get_permissions_for_user, \
    patch_response_for_inline_editing, get_formatted_match


def cms_page(request, path):
    """
    Public interface to the minimal cms page view.
    """
    if not path.startswith('/'):
        path = '/' + path
    site, site_config = get_current_site_and_config(request)
    missing_prefix_in_request = False
    if site_config:
        if site_config.path_prefix:
            if path.startswith(site_config.path_prefix):
                path = path[len(site_config.path_prefix):]
            else:
                missing_prefix_in_request = True
    try:
        page = get_object_or_404(Page, path=path, sites=site.id)
    except Http404:
        if not path.endswith('/') and settings.APPEND_SLASH:
            path += '/'
            page = get_object_or_404(Page, path=path, sites=site.id)
        else:
            raise

    if missing_prefix_in_request:
        # Redirect to fully qualified path according to site settings when the page with given path exists, but we
        # attempt to reach it without the expected site prefix. This happens whenever internal Django functions use
        # Page.get_absolute_url(). The page model has no knowledge of the site configuration since it may vary from
        # one request to another.
        # Since the prefix can be changed dynamically, we use a temporary redirect.
        return HttpResponseRedirect(site_config.path_prefix + path)

    # Attach site configuration to page to render.
    setattr(page, 'site_config', site_config)

    return render_cms_page(request, page)


@csrf_protect
def render_cms_page(request, page):
    """
    Internal interface to the page view.
    """
    # If registration is required for accessing this page, and the user isn't
    # logged in, redirect to the login page.
    if page.registration_required and not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.path)

    response = get_or_create_rendered_page(request, page)
    return response


@require_POST
def add_page_item(request, page_pk):
    page = get_object_or_404(Page, pk=page_pk)
    new_item = PageItem.objects.create(content="")
    PageItemLayout.objects.create(page=page, item=new_item)
    return redirect('%s#item_edit_%i' % (request.META['HTTP_REFERER'], new_item.pk))


# Right now, each item is rendered directly via a model method (not a dedicated template tag) without any request
# context. Therefore, we cannot generate the csrf token.
@csrf_exempt
@require_POST
def swap_item_positions(request, first_item_pk, second_item_pk, page_pk):
    first_layout = get_object_or_404(PageItemLayout, item_id=first_item_pk, page_id=page_pk)
    second_layout = get_object_or_404(PageItemLayout, item_id=second_item_pk, page_id=page_pk)
    priority_of_first_item = first_layout.priority
    priority_of_second_item = second_layout.priority
    first_was_created_before_second = first_layout.item.created < second_layout.item.created
    if priority_of_first_item is None:
        if priority_of_second_item is None:
            # First created before second (first in priority)?
            if first_was_created_before_second:
                priority_of_first_item = 200
                priority_of_second_item = 100
            else:
                priority_of_first_item = 100
                priority_of_second_item = 200
        else:
            if first_was_created_before_second:
                # We want first to go after second.
                priority_of_first_item = priority_of_second_item + 1
            else:
                # We want second to go after first
                priority_of_first_item = priority_of_second_item - 1
    else:
        if priority_of_second_item is None:
            if first_was_created_before_second:
                # We want first to go after second.
                priority_of_second_item = priority_of_first_item - 1
            else:
                # We want second to go after first
                priority_of_second_item = priority_of_first_item + 1
    if priority_of_second_item == priority_of_first_item:
        if first_was_created_before_second:
            # We want first to go after second.
            priority_of_first_item = priority_of_second_item + 1
        else:
            # We want second to go after first
            priority_of_first_item = priority_of_second_item - 1
    else:
        t = priority_of_first_item
        priority_of_first_item = priority_of_second_item
        priority_of_second_item = t

    # Warning, without touching all orders, we might move from several positions in one go due to other items with
    # same priority.
    first_layout.priority = priority_of_first_item
    second_layout.priority = priority_of_second_item
    first_layout.save(update_fields=['priority'])
    second_layout.save(update_fields=['priority'])
    return redirect(request.META['HTTP_REFERER'])


def get_or_create_rendered_page(request, page):
    edition_context = get_edition_context(request)

    # Do not cache page when edition is ongoing, when no cache is disabled or when the page is customized via special
    # query arguments (filtering, etc.)
    can_be_cached = not edition_context['is_editing'] and page.cache_timeout != PAGE_CACHE_DURATIONS.none and not any(request.GET.values())

    page_cache_key = None
    pages_cache = None
    if can_be_cached:
        pages_cache = get_pages_cache()
        page_cache_key = get_page_cache_key(request, page)
        cached_page = pages_cache.get(page_cache_key)
        if cached_page:
            return cached_page

    response = create_rendered_page(request, page, edition_context)

    # Update cache IFF necessary.
    if page_cache_key:
        if not page.enable_client_side_caching:
            # The caching is done on the server only, not on the client-side. Otherwise we might end up showing
            # obsolete data to the user despite the efforts to always return up to date pages on this app (the
            # browser won't even bother asking the server!).
            patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True)
        # Cache rendered page for requested amount of time.
        pages_cache.set(page_cache_key, response, page.get_page_timeout_in_seconds())

    return response


def get_edition_context(request):
    """@:return a tuple of two flags (can_edit, is_editing) according to request query args and current user permissions."""
    permissions = get_permissions_for_user(request.user)
    can_edit = any(permissions.values())
    is_editing = can_edit and request.GET.get(IS_EDITING_ATTRIBUTE_NAME, '0') == '1'
    return dict(**permissions, can_edit=can_edit, is_editing=is_editing)


def create_rendered_page(request, page, edition_context: Mapping[str, bool]):
    context = make_page_rendering_context(request, page, edition_context)
    response = TemplateResponse(request, template=page.template.name, context=context)
    response.render()
    if edition_context['is_editing'] or edition_context['can_edit']:
        patch_response_for_inline_editing(request, page, edition_context, response)
    return response


def make_page_rendering_context(request, page, edition_context: Mapping[str, bool]):
    page.title = page.title

    items = PageItem.objects.get_items_for_page(page, is_editing=edition_context['is_editing'])

    # Handle item filtering based on query.
    tag_filter = request.GET.get('tag')
    if tag_filter:
        items = items.filter(tags__name=tag_filter)

    # Build page, layout and ordered item data.
    layouts = PageItemLayout.objects.filter(page=page, item__in=items).select_related('item')
    layout_by_item_dict = dict()
    zones = set()
    for layout in layouts:
        layout_by_item_dict[layout.item_id] = layout
        zones.add(layout.zone_name)
    items_by_zone_dict = dict()
    all_items = []
    for layout in layouts:
        # Attach page and layout attributes to item for rendering.
        c = layout.item
        setattr(c, 'page', page)
        layout = layout_by_item_dict[c.id]
        setattr(c, 'layout', layout)
        setattr(c, EDITION_CONTEXT_ATTRIBUTE_NAME, edition_context)
        items_by_zone_dict.setdefault(c.layout.zone_name or 'none', []).append(c)
        all_items.append(c)

    # Setup 'previous_item' and 'previous_item' attributes for each item on a per zone basis.
    for zone, items_for_zone in items_by_zone_dict.items():
        zone_count = len(items_for_zone)
        if zone_count > 1:
            for i, c in enumerate(items_for_zone):
                setattr(c, 'previous_item', items_for_zone[(i - 1) % zone_count])
                setattr(c, 'next_item', items_for_zone[(i + 1) % zone_count])
                setattr(c, 'item_count', zone_count)
                setattr(c, 'item_index', i + 1)
        else:
            setattr(c, 'item_count', 1)
            setattr(c, 'item_index', 1)

    any_gag_filter_label = ugettext("Any tag")
    context = dict(
        page=page,
        items_by_zone=items_by_zone_dict,
        all_items=all_items,
        zones=zones,
        layouts=layouts,
        tags_related_to_page=Tag.objects.get_tags_related_to_page(page=page, is_editing=edition_context['is_editing']),
        tag_filter_reset_link=format_html('<a href="{}" class="{}">{}</a>', request.path, 'reset-tag-filter tag-filter-link', any_gag_filter_label) if tag_filter else any_gag_filter_label,
        active_tag_filter=tag_filter,
        base_url=get_base_url_for_page(page, request),
        search_form=SearchContentsForm(),
        search_url=reverse('flexipages:search_results'),
    )
    context.update(edition_context)
    return context


def search_results(request):
    search_results = []
    to_search = None
    if request.method == 'POST':
        search_form = SearchContentsForm(request.POST)
        if search_form.is_valid():
            to_search = search_form.cleaned_data['items']
            if to_search:
                items = PageItem.objects.get_published_items().filter(Q(content__icontains=to_search) | Q(title__icontains=to_search))
                for item in items:
                    pages = Page.objects.get_pages_for_request(request).filter(pageitemlayout__item=item)
                    match = get_formatted_match(text=item.title, to_search=to_search)
                    if not match:
                        # Strip tags and search in plain text.
                        text = striptags(item.content)
                        match = get_formatted_match(text=text, to_search=to_search)
                    if match:
                        search_results.append(dict(item=item, pages=pages, match=match))
    else:
        search_form = SearchContentsForm(request.GET)
    site, site_config = get_current_site_and_config(request)
    base_url = request.path[:-len(SEARCH_RESULTS_PATH)].rstrip('/')
    if base_url:
        base_url = '%s/%s' % (base_url, site_config.path_prefix)
    else:
        base_url = site_config.path_prefix
    context = dict(
        base_url=base_url,
        search_form=search_form,
        search_url=request.path,
        search_results=search_results,
        to_search=to_search,
    )
    return render(request, template_name=site_config.search_results_template.name or 'flexipages/pages/search_results.html', context=context)


@login_required
def ajax_get_last_page_update(request):
    page = get_object_or_404(Page, pk=request.GET.get('page_pk'))
    return JsonResponse(data=dict(last_updated_timestamp=page.last_updated.timestamp()))
