from django.db import models


# Create your models here.
class Species(models.Model):
    """ species.txt schema"""
    ek_species = models.IntegerField(verbose_name='species in ek id', primary_key=True)
    name_short = models.CharField(verbose_name='charater abbreviation of current species', max_length=5)
    name_long = models.CharField(verbose_name='species long latin name', max_length=100)
    current_gtf = models.CharField(verbose_name='current gene annotation file in use', max_length=100)

    class Meta:
        ordering = ['ek_species']

    def __str__(self) -> str:
        return self.name_long


class ID_Mapper(models.Model):
    """ id_mapper_xxx.txt schema"""
    ek_gene_id = models.BigIntegerField(verbose_name='EK_GENE_ID', primary_key=True)
    species = models.ForeignKey(to='Species', to_field='ek_species', on_delete=models.CASCADE, default=-1)
    #
    gene_id = models.CharField(verbose_name='ensembl gene id', max_length=50, null=True)
    ensembl_symbol = models.CharField(verbose_name='ensembl symbol', max_length=50, null=True)
    #
    entrez_id = models.CharField(verbose_name='entrez gene id', max_length = 50, null=True)
    ncbi_symbol = models.CharField(verbose_name='ncbi symbol', max_length=50, null=True)
    #
    vgnc_id = models.CharField(verbose_name='vgnc id', max_length=50, null=True)
    vgnc_symbol = models.CharField(verbose_name='vgnc symbol', max_length=50, null=True)
    #
    hgnc_orthologs = models.CharField(verbose_name='hgnc orthologs id', max_length=50, null=True)
    human_gene_id = models.CharField(verbose_name='human ensembl gene id', max_length=50, null=True)
    human_entrez_id = models.CharField(verbose_name='human gene entrez identifier', max_length = 50, null=True)
    hgnc_symbol = models.CharField(verbose_name='hgnc human orthologs gene symbol', max_length=50, null=True)
    

    class Meta:
        ordering = ['ek_gene_id']

    def __str__(self) -> str:
        return self.gene_id #+ str(self.entrez_id)


class Gene(models.Model):
    """  genes_xxd.txt schema """
    seqname = models.CharField(verbose_name='chromosome', max_length=5)
    start = models.IntegerField(verbose_name='gene start coordinates')
    end = models.IntegerField(verbose_name='gene end coordinates')
    strand = models.CharField(verbose_name='strand', max_length=1)
    gene_biotype = models.CharField(verbose_name='gene biotype', max_length=50)
    ek_gene = models.ForeignKey(to='ID_Mapper', to_field='ek_gene_id', on_delete=models.CASCADE, default=-1)
    species = models.ForeignKey(to='Species', to_field='ek_species', on_delete=models.CASCADE, default=-1)

    class Meta:
        indexes = [models.Index(fields=['seqname', 'start', 'end'])]
        ordering = ['ek_gene']

    def __str__(self) -> str:
        return str(self.ek_gene)


class Exon(models.Model):
    """ exons_xxx.txt schema"""
    ek_gene = models.ForeignKey(to='ID_Mapper', to_field='ek_gene_id', on_delete=models.CASCADE, default=-1)
    exon_id = models.CharField(verbose_name='ensembl exon id', max_length=20)
    start = models.IntegerField(verbose_name='exon start coordinates')
    end = models.IntegerField(verbose_name='exon end coordinates')
    gene_biotype = models.CharField(verbose_name='gene biotype', max_length=50)
    strand = models.CharField(verbose_name='strand', max_length=1)
    transcript_id = models.TextField(verbose_name='corresponding ens transcript id')

    class Meta:
        indexes = [models.Index(fields=['ek_gene', 'start', 'end'])]
        ordering = ['exon_id']

    def __str__(self) -> str:
        return self.exon_id


class ComputedFeatures(models.Model):
    """  computed_feature_xxx.csv schema"""
    ek_gene = models.ForeignKey(to='ID_Mapper', to_field='ek_gene_id', on_delete=models.CASCADE, default=-1)
    feature = models.CharField(max_length=25)
    start = models.IntegerField(verbose_name='current computed feature start coordinates')
    end = models.IntegerField(verbose_name='current computed feature end coordinates')
    gene_biotype = models.CharField(verbose_name='gene biotype', max_length=50, null=True)
    strand = models.CharField(verbose_name='strand', max_length=1, null=True)

    class Meta:
        indexes = [models.Index(fields=['ek_gene', 'start', 'end'])]
        ordering = ['ek_gene']

    def __str__(self) -> str:
        return str(self.ek_gene) + ': ' + self.feature + ' ' + str(self.start) + ' - ' + str(self.end)


class Feature(models.Model):
    """ features_xxx.txt schema"""
    ek_gene = models.ForeignKey(to='ID_Mapper', to_field='ek_gene_id', on_delete=models.CASCADE, default=-1)
    feature = models.CharField(verbose_name='feature annotation in gtf', max_length=16)
    start = models.IntegerField(verbose_name='feature start coordinates')
    end = models.IntegerField(verbose_name='feature end coordinates')
    gene_biotype = models.CharField(verbose_name='gene biotype', max_length=50)
    strand = models.CharField(verbose_name='strand', max_length=1)

    class Meta:
        indexes = [models.Index(fields=['ek_gene', 'start', 'end'])]
        ordering = ['ek_gene']

    def __str__(self) -> str:
        return str(self.ek_gene) + ' - ' + self.feature


class Pathway_Meta(models.Model):
    """ pathway_meta_xxx.txt schema """
    pathway_meta_id = models.IntegerField(verbose_name='database unit meta_data id', primary_key=True)
    species = models.CharField(verbose_name='current species', max_length=10)
    name = models.CharField(verbose_name='current db unit name', max_length=20)
    id_type = models.CharField(verbose_name='the id type of the current db unit', max_length=50)
    update_time = models.CharField(verbose_name='current db unit update time', max_length=20)

    def __str__(self) -> str:
        return str(self.name + ' - ' + self.species)


class Pathway(models.Model):
    """  pathways_xxx.txt schema"""
    ek_pathway_id = models.BigIntegerField(verbose_name='EK_PATHWAY_ID', primary_key=True)
    pathway_id = models.CharField(verbose_name='pathway id in corresponding db', max_length=20)
    pathway_description = models.TextField()
    pathway_meta = models.ForeignKey(to='Pathway_Meta', to_field='pathway_meta_id', on_delete=models.CASCADE, default=-1)

    class Meta:
        ordering = ['ek_pathway_id']

    def __str__(self) -> str:
        return self.pathway_id


class Involve(models.Model):
    """ involve.txt  schema"""
    ek_gene = models.ForeignKey(to='ID_Mapper', to_field='ek_gene_id', on_delete=models.CASCADE, default=-1)
    ek_pathway = models.ForeignKey(to='Pathway', to_field='ek_pathway_id', on_delete=models.CASCADE, default=-1)

    def __str__(self) -> str:
        return self.ek_gene

class InvolveM(models.Model):
    """ involve_msigdb.txt  schema"""
    human_entrez_id = models.BigIntegerField(verbose_name='human entrez for msigdb',default=-1)
    ek_pathway = models.ForeignKey(to='Pathway', to_field='ek_pathway_id', on_delete=models.CASCADE, default=-1)
    bta = models.CharField(verbose_name='ensembl gene id for bta', max_length=50, null=True)
    cap = models.CharField(verbose_name='ensembl gene id for cap', max_length=50, null=True)
    equ = models.CharField(verbose_name='ensembl gene id for equ', max_length=50, null=True)
    gal = models.CharField(verbose_name='ensembl gene id for gal', max_length=50, null=True)
    ovi = models.CharField(verbose_name='ensembl gene id for ovi', max_length=50, null=True)
    sus = models.CharField(verbose_name='ensembl gene id for sus', max_length=50, null=True)


class Task(models.Model):
    """ record all jobs received and store results information"""
    jobid = models.CharField(verbose_name='unique id of each job received', max_length=100, primary_key=True)
    time = models.DateTimeField(verbose_name='time of job received', auto_now_add=True)
    user_email = models.EmailField(verbose_name='user email', max_length=100, null=True)
    status = models.IntegerField(verbose_name='complete 1; fail 0. default 0',default=0)
    list_of_workers = models.TextField(verbose_name='a list of task ids that were spawned',null = True)


    # input
    species = models.CharField(verbose_name='the species the user is working', max_length=10,null=True)
    options = models.CharField(verbose_name='the input parameters of the current job', max_length=256,null=True)
    input_url = models.URLField(verbose_name='url of job input storage', max_length=500, null=True)
    input_content = models.FileField(upload_to='input/', verbose_name='txt file of job input', null=True)

    # output
    url = models.URLField(verbose_name='url of job results storage', max_length=500, null=True)
    csv = models.FileField(upload_to='results/', verbose_name='csv file of job results', null=True)
    
    def delete(self, using=None, keep_parents=False):
        self.input_content.storage.delete(self.input_content.name)
        self.csv.storage.delete(self.csv.name)
        super().delete()

    def __str__(self) -> str:
        return self.jobid