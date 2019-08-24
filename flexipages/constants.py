from collections import namedtuple

FLEXIPAGES_EDITOR_GROUP_NAME = 'FlexiPages Editor'
FLEXIPAGES_ADMIN_GROUP_NAME = 'FlexiPages Administrator'
FLEXIPAGES_SITE_DESIGNER_GROUP_NAME = 'FlexiPages Site Designer'

IS_EDITING_ATTRIBUTE_NAME = 'is_editing'
EDITION_CONTEXT_ATTRIBUTE_NAME = 'edition_context'

SEMANTIC_UI_CSS_URL = "https://cdn.jsdelivr.net/npm/semantic-ui@2.4.2/dist/semantic.min.css"

PAGE_CACHE_DURATIONS = namedtuple("PAGE_CACHE_DURATIONS", "none one_minute five_minutes fifteen_minutes thirty_minutes one_hour three_hours six_hours twelve_hours one_day three_days one_week two_weeks one_month")._make(range(14))

SEARCH_RESULTS_PATH = 'search/'
