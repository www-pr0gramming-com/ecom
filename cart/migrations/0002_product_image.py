# Generated by Django 3.2.12 on 2022-03-14 06:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(default='', upload_to='product_images/'),
            preserve_default=False,
        ),
    ]
