from django.conf import settings
from django.core.cache import caches


def get_pages_cache():
    return caches[settings.FLEXIPAGES_PAGES_CACHE_ALIAS or 'default']


def get_page_cache_keys(page):
    return [get_page_cache_key_for_device(page, device) for device in ('desktop', 'mobile', 'tablet')]


def get_page_cache_key_for_device(page, device):
    return 'flexipages|page=%s|device=%s' % (page.pk, device)


def get_page_cache_key(request, page):
    # Get device key, so that the response has the proper layout if the user browses the site from his phone and
    # his computer at the same time.
    device = 'desktop'
    if getattr(request, 'user_agent', None):
        if request.user_agent.is_mobile:
            device = 'mobile'
        elif request.user_agent.is_tablet:
            device = 'tablet'
    return get_page_cache_key_for_device(page, device)


def delete_cache_for_page(page):
    pages_cache = get_pages_cache()
    pages_cache.delete_many(get_page_cache_keys(page))
