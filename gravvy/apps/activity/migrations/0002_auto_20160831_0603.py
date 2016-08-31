# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='verb',
            field=models.CharField(max_length=50, verbose_name='verb', choices=[(b'add', 'add'), (b'delete', 'delete'), (b'follow', 'start following'), (b'invite', 'invite'), (b'leave', 'left'), (b'like', 'like'), (b'play', 'play'), (b'post', 'post'), (b'share', 'share'), (b'stop-following', 'stop following'), (b'unlike', 'unlike'), (b'unshare', 'unshare')]),
        ),
    ]
