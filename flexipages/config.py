from djangocodemirror.settings import *

FLEXIPAGES_PAGES_CACHE_ALIAS = None

FLEXIPAGES_REQUIRED_APPS = [
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'ckeditor',
    'dbtemplates',
    'djangocodemirror',
    'django_user_agents',
    'rules',
]

CKEDITOR_CONFIGS = {
    'default': {
        'disableNativeSpellChecker': False,
        'entities': False,
        'width': '100%',
        'height': '500px',
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Maximize', 'ShowBlocks', '-', 'Source'],
            ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo'],
            ['Find', 'Replace'],
            ['Styles', 'Format', 'Font', 'FontSize'],
            ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'CopyFormatting',
             '-', 'TextColor', 'BGColor', '-', 'RemoveFormat'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', '-',
             'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink', 'Anchor', 'Image', 'Table', 'HorizontalRule', 'Smiley', 'SpecialChar'],
        ]
    }
}

# CodeMirror

# DB Templates

DBTEMPLATES_ADD_DEFAULT_SITE = False
DBTEMPLATES_AUTO_POPULATE_CONTENT = False
DBTEMPLATES_USE_CODEMIRROR = False
