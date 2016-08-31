# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('verb', models.CharField(max_length=50, verbose_name='verb', choices=[(b'add', 'add'), (b'delete', 'delete'), (b'follow', 'start following'), (b'invite', 'invite'), (b'leave', 'lef'), (b'like', 'like'), (b'play', 'play'), (b'post', 'post'), (b'share', 'share'), (b'stop-following', 'stop following'), (b'unlike', 'unlike'), (b'unshare', 'unshare')])),
                ('object_id', models.PositiveIntegerField(db_index=True, null=True, blank=True)),
                ('target_id', models.PositiveIntegerField(db_index=True, null=True, blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='activity timestamp/date created', db_index=True)),
                ('actor', models.ForeignKey(related_name='activities', verbose_name='actor', to=settings.AUTH_USER_MODEL)),
                ('object_content_type', models.ForeignKey(related_name='object', blank=True, to='contenttypes.ContentType', null=True)),
                ('target_content_type', models.ForeignKey(related_name='target', blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
    ]
