from django.contrib.sitemaps.views import sitemap
from django.urls import path

from flexipages import views
from flexipages.constants import SEARCH_RESULTS_PATH
from flexipages.sitemaps import FlexiPagesSitemap

app_name = "flexipages"

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': {'flexipages': FlexiPagesSitemap}}, name='flexipages.sitemaps.'),
    path('add_page_item/<int:page_pk>/', views.add_page_item, name='add_page_item'),
    path('swap_content_<int:first_item_pk>_with_<int:second_item_pk>_on_page_<int:page_pk>/', views.swap_item_positions, name='swap_item_positions'),
    path(SEARCH_RESULTS_PATH, views.search_results, name='search_results'),
    path('ajax/get_last_page_update/', views.ajax_get_last_page_update, name='ajax_get_last_page_update'),
    path('<path:path>', views.cms_page),
]
