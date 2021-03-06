# Generated by Django 2.1.12 on 2019-09-22 20:55

from django.conf import settings
import django.contrib.sites.managers
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import flexipages.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dbtemplates', '0001_initial'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(db_index=True, help_text='The path of the URL to access this page.', max_length=100, verbose_name='path')),
                ('title', models.CharField(max_length=256, verbose_name='title')),
                ('registration_required', models.BooleanField(default=False, help_text='If this is checked, only logged-in users will be able to view the page.', verbose_name='registration required')),
                ('cache_timeout', models.PositiveSmallIntegerField(choices=[(0, 'no caching'), (1, '1 minute'), (2, '5 minutes'), (3, '15 minutes'), (4, '30 minutes'), (5, '1 hour'), (6, '3 hours'), (7, '6 hours'), (8, '12 hours'), (9, '1 day'), (10, '3 days'), (11, '1 week'), (12, '2 weeks'), (13, '1 month')], default=5, help_text='Indicates for how long the page is cached on the server side.', verbose_name='page cache timeout')),
                ('enable_client_side_caching', models.BooleanField(default=True, help_text="Tells whether the client's browser is allowed to keep this page in cache. When enabled, the user needs to fully refresh the page in his web browser for obtaining the latest version.", verbose_name='enable client side caching')),
                ('description', models.CharField(blank=True, help_text='A description of this page.', max_length=256, verbose_name='description')),
                ('priority', models.PositiveSmallIntegerField(blank=True, default=0, help_text='The page priority for navigation. Lowest priority comes first. A blank field means that the page should not appears in navigation bars.', null=True, verbose_name='priority')),
                ('level', models.PositiveSmallIntegerField(default=0, editable=False, verbose_name='level')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('last_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('parent', models.ForeignKey(default=None, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='flexipages.Page', verbose_name='parent')),
                ('sites', models.ManyToManyField(help_text='The sites on which the URL of this page must be available.', to='sites.Site', verbose_name='sites')),
            ],
            options={
                'verbose_name': 'page',
                'verbose_name_plural': 'pages',
                'ordering': ('level', 'priority', 'path'),
            },
        ),
        migrations.CreateModel(
            name='PageItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(help_text='The content of this item.', max_length=1000000.0, verbose_name='content')),
                ('description', models.CharField(blank=True, help_text='Short description of this content', max_length=256, verbose_name='description')),
                ('title', models.CharField(blank=True, default='', help_text='An optional title for this content.', max_length=128, verbose_name='title')),
                ('publishing_start_date', models.DateField(blank=True, default=None, help_text='Indicates when this item must be published. A blank field means that this content is unpublished and therefore not displayed anywhere.', null=True, verbose_name='publishing start date')),
                ('publishing_end_date', models.DateField(blank=True, default=None, help_text='Indicates when the publication of this content should be over. A blank field means that this content will by available forever.', null=True, verbose_name='publishing end date')),
                ('content_rendering_mode', models.PositiveSmallIntegerField(choices=[(1, 'HTML'), (2, 'Django Template'), (3, 'Markdown'), (4, 'JSON'), (5, 'JavaScript')], default=1, help_text='Indicates whether the content is interpreted and rendered as a Django template, raw HTML, Markdown, etc.', verbose_name='content rendering mode')),
                ('use_wysiwyg_editor', models.BooleanField(default=True, help_text='Indicates whether the content should be rendered with a WYSIWYG editor for HTML.', verbose_name='use WYSIWYG editor')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('last_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('author', models.ForeignKey(blank=True, help_text='The author of this item.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authors_items', to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('last_edited_by', models.ForeignKey(blank=True, help_text='The edited items of the author.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='edited_items', to=settings.AUTH_USER_MODEL, verbose_name='last edited by')),
            ],
            options={
                'verbose_name': 'page item',
                'verbose_name_plural': 'page items',
            },
        ),
        migrations.CreateModel(
            name='PageItemLayout',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.SmallIntegerField(blank=True, default=None, help_text='The priority for the selected item on the given page, and the given zone if defined. Lowest priority comes first. An empty field implies that items are sorted by reversed chronological order of items creation.', null=True, verbose_name='priority')),
                ('zone_name', models.SlugField(blank=True, default='', help_text='The name of the page area that this item belongs to.', verbose_name='zone name')),
                ('item', models.ForeignKey(help_text='The item that we want to locate on the given page.', on_delete=django.db.models.deletion.CASCADE, to='flexipages.PageItem', verbose_name='item')),
                ('page', models.ForeignKey(help_text='The page where the item must be displayed.', on_delete=django.db.models.deletion.CASCADE, to='flexipages.Page', verbose_name='page')),
            ],
            options={
                'verbose_name': 'page item layout',
                'verbose_name_plural': 'page item layouts',
                'ordering': ['page', 'zone_name', 'priority', '-item__created'],
            },
        ),
        migrations.CreateModel(
            name='SiteConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path_prefix', models.CharField(blank=True, default='', help_text="The default path prefix for serving the pages. All pages will be served relative to this prefix. For instance a page with path '/home' will be served under '/cms/home' if the prefix is set to '/cms'.", max_length=128, validators=[flexipages.models.validate_path_prefix], verbose_name='path prefix')),
            ],
            options={
                'verbose_name': 'site configuration',
                'verbose_name_plural': 'sites configuration',
                'ordering': ['site__name'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=64, unique=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'tag',
                'verbose_name_plural': 'tags',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PageTemplate',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('dbtemplates.template',),
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('on_site', django.contrib.sites.managers.CurrentSiteManager('sites')),
            ],
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='search_results_template',
            field=models.ForeignKey(help_text='The template used for displaying search results.', on_delete=django.db.models.deletion.PROTECT, to='flexipages.PageTemplate', verbose_name='search results template'),
        ),
        migrations.AddField(
            model_name='siteconfiguration',
            name='site',
            field=models.OneToOneField(help_text='The site to configure.', on_delete=django.db.models.deletion.CASCADE, to='sites.Site', verbose_name='site'),
        ),
        migrations.AddField(
            model_name='pageitem',
            name='tags',
            field=models.ManyToManyField(blank=True, to='flexipages.Tag', verbose_name='tags'),
        ),
        migrations.AddField(
            model_name='page',
            name='tags',
            field=models.ManyToManyField(blank=True, to='flexipages.Tag', verbose_name='tags'),
        ),
        migrations.AddField(
            model_name='page',
            name='template',
            field=models.ForeignKey(help_text='The template used to render the page.', on_delete=django.db.models.deletion.PROTECT, to='flexipages.PageTemplate', verbose_name='template'),
        ),
        migrations.AlterUniqueTogether(
            name='pageitemlayout',
            unique_together={('page', 'item')},
        ),
    ]
