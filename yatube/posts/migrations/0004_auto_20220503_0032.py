# Generated by Django 2.2.9 on 2022-05-02 21:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0003_auto_20220502_2338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='description',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]
