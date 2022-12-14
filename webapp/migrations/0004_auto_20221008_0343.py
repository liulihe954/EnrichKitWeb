# Generated by Django 3.2.15 on 2022-10-08 03:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0003_auto_20221004_2139'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='involve',
            name='ek_gene_id',
        ),
        migrations.AddField(
            model_name='involve',
            name='ek_gene',
            field=models.ForeignKey(default=-1, on_delete=django.db.models.deletion.CASCADE, to='webapp.id_mapper'),
        ),
        migrations.CreateModel(
            name='InvolveM',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ek_gene_id', models.BigIntegerField(verbose_name='some gene identifier: human entrez for msigdb; ek_gene_id for other')),
                ('ek_pathway', models.ForeignKey(default=-1, on_delete=django.db.models.deletion.CASCADE, to='webapp.pathway')),
            ],
        ),
    ]
