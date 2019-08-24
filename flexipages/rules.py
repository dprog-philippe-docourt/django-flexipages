import rules

from rules import is_superuser


# An full admin is also a restricted admin logically speaking, but full admins only belong to the full admin group.
# Therefore, writing is_mygym_restricted_admin to detect whether a full admin is at least a restricted admin won't work!
from flexipages.constants import FLEXIPAGES_EDITOR_GROUP_NAME, FLEXIPAGES_SITE_DESIGNER_GROUP_NAME, FLEXIPAGES_ADMIN_GROUP_NAME

is_cms_admin = rules.is_group_member(FLEXIPAGES_ADMIN_GROUP_NAME)
is_cms_editor = rules.is_group_member(FLEXIPAGES_EDITOR_GROUP_NAME)
is_cms_designer = rules.is_group_member(FLEXIPAGES_SITE_DESIGNER_GROUP_NAME)


# Special general managers.
# NB: It is required to be able to manage notifications in order to fully manage events (i.e. create and send
# invitation, reminders, schedule, etc.). Therefore, any events manager is can implicitly manage notifications.
can_edit_content = is_superuser or is_cms_admin or is_cms_designer or is_cms_editor,
can_edit_template = is_superuser or is_cms_designer,
can_edit_page = is_superuser or is_cms_admin


# Standard permissions.

rules.add_perm('flexipages.add_page', can_edit_page)
rules.add_perm('flexipages.change_page', can_edit_page)
rules.add_perm('flexipages.delete_page', can_edit_page)
rules.add_perm('flexipages.view_page', can_edit_content)

rules.add_perm('flexipages.add_pageitem', can_edit_content)
rules.add_perm('flexipages.change_pageitem', can_edit_content)
rules.add_perm('flexipages.delete_pageitem', can_edit_content)
rules.add_perm('flexipages.view_pageitem', can_edit_content)

rules.add_perm('flexipages.add_pageitemlayout', can_edit_content)
rules.add_perm('flexipages.change_pageitemlayout', can_edit_content)
rules.add_perm('flexipages.delete_pageitemlayout', can_edit_content)
rules.add_perm('flexipages.view_pageitemlayout', can_edit_content)

rules.add_perm('flexipages.add_pagetemplate', can_edit_template)
rules.add_perm('flexipages.change_pagetemplate', can_edit_template)
rules.add_perm('flexipages.delete_pagetemplate', can_edit_template)
rules.add_perm('flexipages.view_pagetemplate', can_edit_content)

rules.add_perm('flexipages.add_siteconfiguration', is_cms_admin)
rules.add_perm('flexipages.change_siteconfiguration', is_cms_admin)
rules.add_perm('flexipages.delete_siteconfiguration', is_cms_admin)
rules.add_perm('flexipages.view_siteconfiguration', can_edit_content)
