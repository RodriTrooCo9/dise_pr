# Generated by Django 5.1.1 on 2024-10-11 01:06

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Registro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('temperatura', models.FloatField()),
                ('humedad', models.FloatField()),
            ],
        ),
    ]
