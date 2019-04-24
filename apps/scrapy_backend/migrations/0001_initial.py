# Generated by Django 2.2 on 2019-04-23 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Artical',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('row_status', models.CharField(default='normal', max_length=64)),
                ('title', models.CharField(max_length=64)),
                ('author', models.CharField(max_length=64)),
                ('keywords', models.CharField(max_length=64)),
                ('description', models.CharField(max_length=64)),
                ('content', models.TextField()),
                ('url', models.CharField(max_length=64)),
                ('share', models.CharField(max_length=64)),
                ('comment', models.CharField(max_length=64)),
                ('timestamp', models.CharField(max_length=64)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]