from celery import shared_task , current_task# , group
from django.db import connection
from webapp import models
from webapp.push_s3 import push_s3
from webapp.send_email import send_email
import itertools
from celery.result import allow_join_result

####
# use async version to handle long request input - run match in parallel + push to s3 + send email
####
@shared_task
def handle_loci_long_request(cur_species, cur_feature_list, cur_cfeature_list, cur_chr_list, cur_coord_list, jobid, user_email):
    # print('handle loci long')
    # step 0 notification email
    send_email(user_email, type='init', jobid=jobid)

    # step 1 do the job in parallel
    # with allow_join_result():
    #     out = group(
    #         loci_match_unit_celery.s(cur_feature_list, cur_cfeature_list, cur_chr, cur_loci) for (cur_chr, cur_loci) in itertools.zip_longest(cur_chr_list, cur_coord_list)
    #     ).apply_async().get()

    with allow_join_result():
        groups = loci_match_unit.chunks(itertools.zip_longest([cur_species] * len(cur_chr_list), [cur_feature_list] * len(cur_chr_list), [cur_cfeature_list] * len(cur_chr_list), cur_chr_list, cur_coord_list), 10).group().apply_async()

        children_list = [task for parents in groups.children for task in parents.as_list()[::-1]]
        
        out = groups.get()
    
    output = list(itertools.chain.from_iterable(list(itertools.chain.from_iterable(out))))

     # gather list of worker ids
    children_list.append(current_task.request.id)

    # step 2 push to s3
    target_url = push_s3(
        output,
        ['Chromosome', 'Coordinates', 'Feature', 'Description', 'Transcript_id ID', 'Ensembl Gene ID', 'Gene Biotype', 'Strand'],
        jobid, children_list)

    # step 3 send email
    view_link_concat = "http://enrichkit.info/results/?jobid=" + jobid

    send_email(user_email, type='finish', view_link=view_link_concat, download_link=target_url)

    return True


####
# for short input, sync version, show results directly
####

@ shared_task
def loci_match_unit(cur_species, cur_feature_list, cur_cfeature_list, cur_chr, cur_loci, upstream_length=10000):

    output = []
    query_count_local = 0

    gene_target = models.Gene.objects.select_related(
            'species'
        ).filter(
            species__name_short = cur_species
        ).filter(
            seqname = cur_chr
        ).filter(
            start__lte = cur_loci + upstream_length
        ).filter(
            end__gte = cur_loci - upstream_length
        )

    print('cur_species - ', cur_species)
    print('cur_chr - ', cur_chr)
    print('cur_loci - ', cur_loci)

    #
    if not gene_target.exists():
        output.append([cur_chr, cur_loci, 'intergeneric or out of bound', '', '', '', ''])
        query_count_local += 1
    else:
        cur_ek_gene_id = gene_target[0].ek_gene_id
        if 'exon' in cur_feature_list:
            # exon
            exon_target = models.Exon.objects.select_related('ek_gene').filter(ek_gene_id=cur_ek_gene_id).filter(start__lte=cur_loci).filter(end__gte=cur_loci)
            if exon_target.exists():
                tmp_target = exon_target[0]
                output.append([cur_chr, cur_loci, 'exonic', tmp_target.exon_id, tmp_target.transcript_id, tmp_target.ek_gene.gene_id, tmp_target.gene_biotype, tmp_target.strand])
                query_count_local += 1

        # feature
        feature_target = models.Feature.objects.select_related(
            'ek_gene').filter(ek_gene_id=cur_ek_gene_id).filter(start__lte=cur_loci).filter(end__gte=cur_loci).filter(feature__in=set(cur_feature_list))
        if feature_target.exists():
            tmp_target = feature_target[0]
            output.append([cur_chr, cur_loci, 'feature', tmp_target.feature, '', tmp_target.ek_gene.gene_id, tmp_target.gene_biotype, tmp_target.strand])
            query_count_local += 1

        # computed feature
        compute_feature_target = models.ComputedFeatures.objects.select_related(
            'ek_gene').filter(ek_gene_id=cur_ek_gene_id).filter(start__lte=cur_loci).filter(end__gte=cur_loci).filter(feature__in=set(cur_cfeature_list))
        if compute_feature_target.exists():
            tmp_target = compute_feature_target[0]
            output.append([cur_chr, cur_loci, 'computed feature', tmp_target.feature, '', tmp_target.ek_gene.gene_id, tmp_target.gene_biotype, tmp_target.strand])
            query_count_local += 1

        # check if not covered
        if query_count_local < 1:
            output.append([cur_chr, cur_loci, 'Not Covered', '', '', '', '', ''])

    connection.close()
    return output

####
# for longer input, async version, push to celery (broker queue)
####


# @ shared_task
def loci_match_unit_celery(cur_species, cur_feature_list, cur_cfeature_list, cur_chr, cur_loci, upstream_length=10000):
    output = []
    query_count_local = 0
    
    gene_target = models.Gene.objects.select_related(
            'species'
        ).filter(
            species__name_short = cur_species
        ).filter(
            seqname = cur_chr
        ).filter(
            start__lte = cur_loci + upstream_length
        ).filter(
            end__gte = cur_loci - upstream_length
        )

    #
    if not gene_target.exists():
        output.append([cur_chr, cur_loci, 'intergeneric or out of bound', '', '', '', ''])
        query_count_local += 1
    else:
        cur_ek_gene_id = gene_target[0].ek_gene_id
        if 'exon' in cur_feature_list:
            # exon
            exon_target = models.Exon.objects.select_related('ek_gene').filter(ek_gene_id=cur_ek_gene_id).filter(start__lte=cur_loci).filter(end__gte=cur_loci)
            if exon_target.exists():
                tmp_target = exon_target[0]
                output.append([cur_chr, cur_loci, 'exonic', tmp_target.exon_id, tmp_target.transcript_id, tmp_target.ek_gene.gene_id, tmp_target.gene_biotype, tmp_target.strand])
                query_count_local += 1

        # feature
        feature_target = models.Feature.objects.select_related(
            'ek_gene').filter(ek_gene_id=cur_ek_gene_id).filter(start__lte=cur_loci).filter(end__gte=cur_loci).filter(feature__in=set(cur_feature_list))
        if feature_target.exists():
            tmp_target = feature_target[0]
            output.append([cur_chr, cur_loci, 'feature', tmp_target.feature, '', tmp_target.ek_gene.gene_id, tmp_target.gene_biotype, tmp_target.strand])
            query_count_local += 1

        # computed feature
        compute_feature_target = models.ComputedFeatures.objects.select_related(
            'ek_gene').filter(ek_gene_id=cur_ek_gene_id).filter(start__lte=cur_loci).filter(end__gte=cur_loci).filter(feature__in=set(cur_cfeature_list))
        if compute_feature_target.exists():
            tmp_target = compute_feature_target[0]
            output.append([cur_chr, cur_loci, 'computed feature', tmp_target.feature, '', tmp_target.ek_gene.gene_id, tmp_target.gene_biotype, tmp_target.strand])
            query_count_local += 1

        # check if not covered
        if query_count_local < 1:
            output.append([cur_chr, cur_loci, 'Not Covered', '', '', '', '', ''])

    connection.close()
    return output
