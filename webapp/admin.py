# from xml.parsers.expat import model
from django.contrib import admin
from . import models

# Register your models here.
@admin.register(models.Species)
class TaskAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = [
        'name_long',
        'name_short',
        'current_gtf'
    ]
    search_fields = ['name_short']


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = [
        'jobid',
        'user_email',
        'status'
    ]
    search_fields = ['jobid']


@admin.register(models.ID_Mapper)
class ID_MapperAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = [
        'gene_id',
        'entrez_id',
        'vgnc_symbol',
        'human_gene_id'
    ]
    list_filter = ['species']
    search_fields = ['gene_id', 'entrez_id', 'vgnc_symbol', 'human_gene_id']


@admin.register(models.Gene)
class GeneAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = [
        'ek_gene',
        'seqname',
        'start',
        'end'
    ]
    list_filter = ['seqname']
    search_fields = ['ek_gene__gene_id', 'seqname', 'start']


@admin.register(models.Exon)
class ExonAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = [
        'exon_id',
        'ek_gene',
        'start',
        'end'
    ]
    search_fields = ['exon_id', 'ek_gene__gene_id']


@admin.register(models.Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = [
        'ek_gene',
        'feature'
    ]
    list_filter = ['feature']
    search_fields = ['ek_gene__gene_id']


@admin.register(models.Pathway_Meta)
class Pathway_MetaAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_filter = ['species', 'update_time']
    search_fields = ['name']


@admin.register(models.ComputedFeatures)
class ComputedFeaturesAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = [
        'ek_gene',
        'feature'
    ]
    list_filter = ['feature']
    search_fields = ['ek_gene__gene_id']


@admin.register(models.Pathway)
class PathwayAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = [
        'pathway_id',
        'pathway_meta',
        'pathway_description'
    ]
    list_filter = ['pathway_meta__name']
    search_fields = ['pathway_description', 'pathway_id', 'pathway_meta__name']
