# Generated by Django 5.1.7 on 2025-05-09 02:11

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('owner', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('name', 'owner')},
            },
        ),
        migrations.CreateModel(
            name='Learning_Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('duration', models.IntegerField(default=-1)),
                ('method', models.CharField(choices=[('new_words', 'New Words'), ('repeat', 'Repeat'), ('test', 'Test')], default='new_words', max_length=20)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='web.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=50)),
                ('translation', models.CharField(max_length=50)),
                ('transcription', models.CharField(max_length=50)),
                ('category', models.ManyToManyField(related_name='words', to='web.category')),
            ],
            options={
                'unique_together': {('word', 'translation', 'transcription')},
            },
        ),
        migrations.CreateModel(
            name='Answer_Attempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_correct', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.learning_session')),
                ('word', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.word')),
            ],
        ),
        migrations.CreateModel(
            name='Learning_Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'category')},
            },
        ),
        migrations.CreateModel(
            name='Learned_Word',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('word', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.word')),
            ],
            options={
                'unique_together': {('user', 'word')},
            },
        ),
        migrations.CreateModel(
            name='Word_Repetition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('next_review', models.DateTimeField(default=datetime.datetime(2025, 5, 9, 2, 12, 28, 795675, tzinfo=datetime.timezone.utc))),
                ('repetition_count', models.PositiveIntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('word', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.word')),
            ],
            options={
                'unique_together': {('user', 'word')},
            },
        ),
    ]
