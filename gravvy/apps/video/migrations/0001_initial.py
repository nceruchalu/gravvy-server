# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import gravvy.apps.video.models
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Clip',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.SmallIntegerField(help_text='0-indexed order in video; 0 means this is the first clip', verbose_name='clip order', validators=[django.core.validators.MinValueValidator(0)])),
                ('mp4', models.FileField(help_text="clip's mp4 file", upload_to=gravvy.apps.video.models.get_clip_mp4_path, verbose_name='mp4')),
                ('photo', models.ImageField(help_text='image of a frame in mp4 that serves as a preview/fallback image', upload_to=gravvy.apps.video.models.get_clip_photo_path, verbose_name='photo')),
                ('duration', models.FloatField(default=0.0, help_text='duration of clip mp4, in seconds.', verbose_name='clip duration')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, help_text='creation date/time', verbose_name='date created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='last update date/time')),
                ('owner', models.ForeignKey(related_name='owned_clips', verbose_name='owner', to=settings.AUTH_USER_MODEL, help_text='clip uploader')),
            ],
            options={
                'ordering': ('order',),
                'verbose_name': 'video clip',
                'verbose_name_plural': 'video clips',
            },
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hash_key', models.CharField(help_text='unique identifier of video object', unique=True, max_length=20, verbose_name='unique hash')),
                ('title', models.CharField(help_text='video title', max_length=200, verbose_name='title', blank=True)),
                ('description', models.CharField(help_text='video details', max_length=1000, verbose_name='description', blank=True)),
                ('photo', models.ImageField(help_text="copy of preview image of video's first clip from its collection of associated clips.", upload_to=gravvy.apps.video.models.get_video_photo_path, verbose_name='photo')),
                ('likes_count', models.IntegerField(default=0, help_text='Number of likes', verbose_name='likes count', validators=[django.core.validators.MinValueValidator(0)])),
                ('plays_count', models.IntegerField(default=0, help_text='Number of plays', verbose_name='plays count', validators=[django.core.validators.MinValueValidator(0)])),
                ('clips_count', models.IntegerField(default=0, help_text='Number of clips', verbose_name='clips count', validators=[django.core.validators.MinValueValidator(0)])),
                ('duration', models.FloatField(default=0.0, help_text='total duration of all clip mp4s, in seconds.', verbose_name='total duration')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, help_text='creation date/time', verbose_name='date created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='last update date/time')),
                ('owner', models.ForeignKey(related_name='owned_videos', verbose_name='owner', to=settings.AUTH_USER_MODEL, help_text="Video's primary owner that can modify its settings")),
            ],
            options={
                'ordering': ['-updated_at'],
                'verbose_name': 'video',
                'verbose_name_plural': 'videos',
            },
        ),
        migrations.CreateModel(
            name='VideoUsers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hash_key', models.CharField(help_text='unique identifier of video user object', unique=True, max_length=20, verbose_name='unique hash')),
                ('status', models.IntegerField(default=0, verbose_name='Video interaction status', choices=[(0, b'Invited'), (1, b'Viewed post-invite'), (2, b'Uploaded a clip')])),
                ('new_likes_count', models.IntegerField(default=0, help_text="count of new video likes that haven't been acknowledged by video user", verbose_name='New likes count', validators=[django.core.validators.MinValueValidator(0)])),
                ('new_clips_count', models.IntegerField(default=0, help_text="count of new video clips that haven't been acknowledged by video user", verbose_name='New clips count', validators=[django.core.validators.MinValueValidator(0)])),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, help_text='Video user creation date/time', verbose_name='date created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='last update date/time')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('video', models.ForeignKey(to='video.Video')),
            ],
            options={
                'ordering': ('-created_at',),
                'verbose_name': 'video user',
                'verbose_name_plural': 'video users',
            },
        ),
        migrations.AddField(
            model_name='video',
            name='users',
            field=models.ManyToManyField(related_name='videos', to=settings.AUTH_USER_MODEL, through='video.VideoUsers', blank=True, help_text='Users associated with video', verbose_name='users'),
        ),
        migrations.AddField(
            model_name='clip',
            name='video',
            field=models.ForeignKey(related_name='clips', verbose_name='video', to='video.Video', help_text='associated video'),
        ),
        migrations.AlterUniqueTogether(
            name='videousers',
            unique_together=set([('video', 'user')]),
        ),
    ]
