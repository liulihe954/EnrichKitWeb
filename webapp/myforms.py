from django import forms
from django.utils.safestring import mark_safe

class My_Loci_Form(forms.Form):
    # SPECIES
    SPECIES_CHOICES = (
        ('bta', 'Cow - Bos Taurus ARS-UCD1.2'),
        ('cap', 'Goat - Capra_hircus ARS1.107'),
        ('ovi', 'Sheep - Ovis_aries Oar_v3.1.107'),
        ('gal', 'Chicken - Gallus_gallus gca000002315v5.GRCg6a.107'),
        ('sus', 'Pig - Sus_scrofa Sscrofa11.1.107'),
        ('equ', 'Horse - Equus_caballus EquCab3.0.107'),
        )
    FEATURE_CHOICES = [
        ('exon', 'Exon'),
        ('start_codon', 'Start Codon'),
        ('stop_codon', 'Stop Codon'),
        ('CDS', 'CDS'),
        ('five_prime_utr', '5\' UTR'),
        ('three_prime_utr', '3\' UTR'),
        ('transcript', 'Transcript')
    ]
    COMPUTATED_FEATURE_CHOICES = [
        # ('upstream', 'Upstream (10k bp default) set'),
        ('upstream', mark_safe('Upstream (10k bp default) set to <input type="text" size="3" method="post" placeholder="10" id="upstream_user_input"> k bp')),
        ('downstream', mark_safe('Downstream (10k bp default) set to <input type="text" size="3" method="post" placeholder="10" id="downstream_user_input"> k bp')),
        ('splice donor', mark_safe('Splice Donor (50 bp default) set to <input type="text" size="3" method="post" placeholder="50" id="splice_donor_input"> bp')),
        ('splice acceptor', mark_safe('Splice Acceptor (50 bp default) set to <input type="text" size="3" method="post" placeholder="50" id="splice_acceptor_input"> bp')),
        # ('splice donor', 'Splice Donor (50 bp default)'),
        # ('splice acceptor', 'Splice Acceptor (50 bp default)'),
        ('intron', 'Intron'),
    ]

    species = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'btn-lg btn-secondary form-input',
                   }),  # btn btn-secondary dropdown-toggle
        choices=SPECIES_CHOICES
    )

    input_features = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'h5 form-input'}),
        choices=FEATURE_CHOICES,
        initial=[c[0] for c in FEATURE_CHOICES])
    #

    computed_features = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'h5 form-input'}),
        choices=COMPUTATED_FEATURE_CHOICES,
        initial=[c[0] for c in COMPUTATED_FEATURE_CHOICES])

    input_loci_list = forms.CharField(required=False,
                                      label="", help_text="",
                                      widget=forms.Textarea(attrs={'rows': 10, 'cols': 40, 'style': 'resize:none;', 'class': 'h5 form-input'}))

    input_loci_file = forms.FileField(required=False)

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input'}),
        label=('Enter your new email'), required=False)


class My_idmap_Form(forms.Form):
    # SPECIES
    SPECIES_CHOICES = (
        ('bta', 'Cow - Bos Taurus ARS-UCD1.2'),
        ('cap', 'Goat - Capra_hircus ARS1.107'),
        ('ovi', 'Sheep - Ovis_aries Oar_v3.1.107'),
        ('gal', 'Chicken - Gallus_gallus gca000002315v5.GRCg6a.107'),
        ('sus', 'Pig - Sus_scrofa Sscrofa11.1.107'),
        ('equ', 'Horse - Equus_caballus EquCab3.0.107'),
    )
    GENE_TYPE_CHOICES = (
        ('ens', 'Ensembl Gene ID'),
        ('entrez_id', 'Entrez Gene ID'),
    )

    species = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'btn-lg btn-secondary', 'id': 'species_input'}),
        choices=SPECIES_CHOICES
    )

    gene_type = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'btn-lg btn-secondary', 'id': 'gene_type_input'}),
        choices=GENE_TYPE_CHOICES
    )

    input_gene_list = forms.CharField(required=False,
                                      label="", help_text="",
                                      widget=forms.Textarea(attrs={'rows': 10, 'cols': 60, 'style': 'resize:none;', 'id': 'gene_list_input'}))

    input_id_file = forms.FileField(required=False)


class My_ORA_Form(forms.Form):
    # SPECIES
    SPECIES_CHOICES = (
        ('bta', 'Cow - Bos Taurus ARS-UCD1.2'),
        ('cap', 'Goat - Capra_hircus ARS1.107'),
        ('ovi', 'Sheep - Ovis_aries Oar_v3.1.107'),
        ('gal', 'Chicken - Gallus_gallus gca000002315v5.GRCg6a.107'),
        ('sus', 'Pig - Sus_scrofa Sscrofa11.1.107'),
        ('equ', 'Horse - Equus_caballus EquCab3.0.107'),
    )
    DB_CHOICES = [
        ('go', 'Gene Ontology(GO)'),
        ('interpro', 'Interpro'),
        ('kegg', 'KEGG'),
        ('mesh', 'Medical Subject Headings (MeSH)'),
        ('reactome', 'Reactome'),
        # ('msigdb', 'Molecular Signatures Database (MSigDB)'),
    ]

    species = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'btn-lg btn-secondary'}),  # btn btn-secondary dropdown-toggle
        choices=SPECIES_CHOICES
    )

    # input_db_test = forms.BooleanField()

    input_db_list = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'h5'}),
        choices=DB_CHOICES,
        initial=[c[0] for c in DB_CHOICES])

    input_gene_list = forms.CharField(required=False,
                                      label="", help_text="",
                                      widget=forms.Textarea(attrs={'rows': 10, 'cols': 60, 'style': 'resize:none;'}))

    input_gene_file = forms.FileField(required=False)

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input'}),
        label=('Enter your new email'), required=False)


class My_Loci_Aggreg_Form(forms.Form):
    # SPECIES
    SPECIES_CHOICES = (
        ('bta', 'Cow - Bos Taurus ARS-UCD1.2'),
        ('cap', 'Goat - Capra_hircus ARS1.107'),
        ('ovi', 'Sheep - Ovis_aries Oar_v3.1.107'),
        ('gal', 'Chicken - Gallus_gallus gca000002315v5.GRCg6a.107'),
        ('sus', 'Pig - Sus_scrofa Sscrofa11.1.107'),
        ('equ', 'Horse - Equus_caballus EquCab3.0.107'),
    )
    METHOD_CHOICES = [
        ('fisher', 'Fisher’s combination test'),
        ('sidak', 'Sidak’s combination test (the best SNP)'),
        ('simes', 'Simes’ combination test'),
        ('fdr', 'The FDR method'),
        # ('msigdb', 'Molecular Signatures Database (MSigDB)'),
    ]

    species = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'btn-lg btn-secondary'}),  # btn btn-secondary dropdown-toggle
        choices=SPECIES_CHOICES
    )

    # input_db_test = forms.BooleanField()

    input_methods_list = forms.MultipleChoiceField(
        widget = forms.CheckboxSelectMultiple(attrs={'class': 'h5'}),
        choices = METHOD_CHOICES,
        initial =[c[0] for c in METHOD_CHOICES])

    input_loci_list = forms.CharField(required=False,
                                      label="", help_text="",
                                      widget=forms.Textarea(attrs={'rows': 10, 'cols': 40, 'style': 'resize:none;', 'class': 'h5 form-input'}))

    input_loci_file = forms.FileField(required=False)

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input'}),
        label=('Enter your new email'), required=False)
