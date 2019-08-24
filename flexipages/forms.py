from django import forms
from django.utils.translation import ugettext_lazy as _

from flexipages.models import PageItem


class SearchContentsForm(forms.ModelForm):
    contents = forms.CharField(label=_('Search'), required=False, widget=forms.TextInput(attrs={'class': 'search-contents-field', 'placeholder': _('Search...'), 'type': 'search'}))

    class Meta:
        model = PageItem
        fields = ('contents',)
