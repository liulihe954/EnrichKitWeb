# Generated by Django 3.2.15 on 2022-10-04 21:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0002_rename_ek_gene_involve_ek_gene_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='id_mapper',
            name='entrez_id',
            field=models.CharField(max_length=50, null=True, verbose_name='entrez gene id'),
        ),
        migrations.AlterField(
            model_name='id_mapper',
            name='human_entrez_id',
            field=models.CharField(max_length=50, null=True, verbose_name='human gene entrez identifier'),
        ),
    ]