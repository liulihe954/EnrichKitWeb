# Generated by Django 3.2.15 on 2022-10-14 02:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0005_auto_20221008_0811'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='csv',
            field=models.FileField(null=True, upload_to='results/', verbose_name='csv file of job results'),
        ),
        migrations.AlterField(
            model_name='task',
            name='input_content',
            field=models.FileField(null=True, upload_to='input/', verbose_name='txt file of job input'),
        ),
    ]
