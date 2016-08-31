# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import gravvy.apps.account.models
import django.utils.timezone
from django.conf import settings
import gravvy.fields.phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('phone_number', gravvy.fields.phonenumber_field.modelfields.PhoneNumberField(help_text='Required. E.164 format phone number.', unique=True, verbose_name='phone number', error_messages={b'unique': 'A user with that phone number already exists.'})),
                ('full_name', models.CharField(max_length=30, verbose_name='full name', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='last update date/time')),
                ('avatar', models.ImageField(upload_to=gravvy.apps.account.models.get_avatar_path, verbose_name='profile picture', blank=True)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'swappable': 'AUTH_USER_MODEL',
                'verbose_name_plural': 'users',
            },
        ),
        migrations.CreateModel(
            name='AuthToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(unique=True, max_length=40)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='creation date/time')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='last update date/time')),
                ('user', models.OneToOneField(related_name='auth_token', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('verification_code', models.PositiveIntegerField(verbose_name='verification code')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, help_text='creation date/time', verbose_name='date created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='last update date/time')),
                ('user', models.OneToOneField(related_name='registration_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'registration profile',
                'verbose_name_plural': 'registration profiles',
            },
        ),
    ]
