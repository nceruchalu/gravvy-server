# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videousers',
            name='status',
            field=models.IntegerField(default=1, verbose_name='Video interaction status', choices=[(1, b'Invited'), (2, b'Viewed post-invite'), (3, b'Uploaded a clip')]),
        ),
    ]
