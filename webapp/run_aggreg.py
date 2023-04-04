from celery import shared_task, current_task
from django.db import connection
from collections import defaultdict
from webapp import models
from webapp.push_s3 import push_s3
from webapp.send_email import send_email
from celery.result import allow_join_result
import itertools
from webapp.aggreg_methods import aggregate

####
# use async version to handle long request input - run match in parallel + push to s3 + send email
####

@shared_task
def handle_loci_aggreg_request(cur_species, cur_methods_list, cur_chr_list, cur_coord_list, cur_pval_list, jobid, user_email):
    # print('handle loci long')
    # step 0 notification email
    send_email(user_email, type='init', jobid=jobid)

    # step 1 do the job in parallel
    # with allow_join_result():
    #     out = group(
    #         loci_match_unit_celery.s(cur_feature_list, cur_cfeature_list, cur_chr, cur_loci) for (cur_chr, cur_loci) in itertools.zip_longest(cur_chr_list, cur_coord_list)
    #     ).apply_async().get()

    with allow_join_result():
        groups = loci_aggreg_unit.chunks(itertools.zip_longest([cur_species] * len(cur_chr_list), cur_chr_list, cur_coord_list, cur_pval_list), 10).group().apply_async()

        children_list = [task for parents in groups.children for task in parents.as_list()[::-1]]
        
        out = groups.get()
    
    # output is a list of list [[gene_id or "-", paval]]
    output = list(itertools.chain.from_iterable(list(itertools.chain.from_iterable(out))))

    # aggregation hashtable 
    aggreg_dict = defaultdict(list)

    for item in output:
        if not item[0] == "-":
            aggreg_dict[item[0]].append(item[1])
        else:
            pass
    # print('cur_methods_list ',cur_methods_list)

    # ## apply different methods to process output and format output
    aggreg_list = []
    for k, v in aggreg_dict.items():
        aggreg_pvals_tmp = []
        for method in cur_methods_list:
            aggreg_pvals_tmp.append(aggregate(v, method))
        tmp_row = [k, '/'.join([str(pval) for pval in v])]
        tmp_row.extend(aggreg_pvals_tmp)
        aggreg_list.append(tmp_row)
        
    # print(aggreg_list)
    # # gather list of worker ids
    children_list.append(current_task.request.id)

    # # # step 2 push to s3
    target_url = push_s3(
        aggreg_list,
        ['Gene ID', 'Raw P-values'] + cur_methods_list,
        jobid, children_list)

    # # # step 3 send email
    view_link_concat = "http://enrichkit.info/results/?jobid=" + jobid

    send_email(user_email, type='finish', view_link=view_link_concat, download_link=target_url)

    return True


@ shared_task
def loci_aggreg_unit(cur_species, cur_chr, cur_loci, cur_pval, upstream_length=10000):

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

    # print('cur_species - ', cur_species)
    # print('cur_chr - ', cur_chr)
    # print('cur_loci - ', cur_loci)

    #
    if not gene_target.exists():
        output.append(['-',cur_pval])
    else:
        cur_gene = models.ID_Mapper.objects.filter(ek_gene_id=gene_target[0].ek_gene_id)
        output.append([str(cur_gene[0]), cur_pval])
        
    connection.close()
    return output
