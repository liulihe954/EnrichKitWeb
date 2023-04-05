import itertools
from webapp import models
from webapp.push_s3 import push_s3
import pandas as pd
import numpy as np
import gseapy as gp
import scipy.stats as stats
from collections import defaultdict
from celery import shared_task, current_task, group
from celery.result import allow_join_result
import concurrent.futures

from webapp.send_email import send_email


@shared_task
def handle_gsea_request(cur_db_list, cur_species, out_gene_list, out_rank_list, jobid, user_email):
    # step 0 notification email
    send_email(user_email, type='init', jobid=jobid)

    # convert to pd df and rank/sort
    gene_ranks = {
            'Gene': out_gene_list,
            'Rank': out_rank_list
        }
    gene_ranks_df = pd.DataFrame(gene_ranks)
    gene_ranks_df = gene_ranks_df.sort_values('Rank', ascending = False).reset_index(drop = True)

    # take the sorted list and pass down (avoid serialization issue)
    out_gene_list_s = gene_ranks_df["Gene"].values.tolist()
    out_rank_list_s = gene_ranks_df["Rank"].values.tolist()

    # prepare output
    output_all = []

    # prepare db list
    filter_db_list = [item for item in cur_db_list]
    
    # do the job in parallel
    with allow_join_result():
        out_t = group(
            gsea_each_db.s(cur_species, db, out_gene_list_s, out_rank_list_s) for db in filter_db_list
        ).apply_async()
        out = out_t.get()

    # mark the children processes id
    children_list = [task for parents in out_t.children for task in parents.as_list()[::-1]]
    # print('others id  ', children_list)

    # collect output
    output_all = list(itertools.chain.from_iterable(out))

    # # gather current task id
    children_list.append(current_task.request.id)

    # push to s3
    target_url = push_s3(
        output_all,
        ['Term ID', 'Source', 'Term Description', 'ES', 'NES', 'P value', 'FDR', 'FWERP', 'TAG%', 'Gene%', 'Lead Genes', 'Matched Genes'],
        jobid, children_list)

    # | {
    # |  Term ID: pathway ID,
    # |  Source: database name
    # |  Term Description: pathway name/description 
    # |  es: enrichment score,
    # |  nes: normalized enrichment score,
    # |  pval:  Nominal p-value (from the null distribution of the gene set,
    # |  fdr: FDR qvalue (adjusted False Discory Rate),
    # |  fwerp: Family wise error rate p-values,
    # |  tag%: Percent of gene set before running enrichment peak (ES),
    # |  gene %: Percent of gene list before running enrichment peak (ES),
    # |  lead_genes: leading edge genes (gene hits before running enrichment peak),
    # |  matched genes: genes matched to the data,
    # | }

    # # step 3 send email
    view_link_concat = "http://enrichkit.info/results/?jobid=" + jobid

    send_email(user_email, type='finish', view_link=view_link_concat, download_link=target_url)

    return True

@shared_task
def gsea_each_db(cur_species, db, out_gene_list_s, out_rank_list_s, type='main'):
    # print('processing %s' % db)
    output = []
    # print('db - ', db)
    if db != 'msigdb':
        cur_pathway_meta_id = models.Pathway_Meta.objects.filter(
            species=cur_species
        ).filter(
            name=db
        ).values('pathway_meta_id', 'name', 'id_type')[0]['pathway_meta_id']

        # use pathway meta to locate one specific db
        cur_db_expanded = models.Involve.objects.select_related(
            'ek_pathway'
        ).filter(
            ek_pathway__pathway_meta=cur_pathway_meta_id
        ).values('ek_pathway__pathway_id', 'ek_pathway__pathway_description', 'ek_gene__gene_id'
                ).order_by('ek_pathway__pathway_id')
        
        cur_db_expanded_df = pd.DataFrame(list(cur_db_expanded))

    else:
        cur_db_expanded = models.InvolveM.objects.values(
            'ek_pathway__pathway_id', 'ek_pathway__pathway_description', cur_species
        ).distinct()
        
        cur_db_expanded_df_raw = pd.DataFrame(list(cur_db_expanded))
        mapping = {cur_db_expanded_df_raw.columns[2]: 'ek_gene__gene_id'}
        cur_db_expanded_df = cur_db_expanded_df_raw.rename(columns=mapping)

    pathway_dict = defaultdict(list)
    cc = 0
    for index, result in cur_db_expanded_df.iterrows():
        cc += 1
        # if cc < 10:
        #     print(result)
        if len(result['ek_gene__gene_id']) >  0:
            pathway_dict['+'.join([result['ek_pathway__pathway_id'], result['ek_pathway__pathway_description']])].append(result['ek_gene__gene_id'])
        if cc % 10000 == 0:
            continue
            # print('processed %d' % cc)
    
        # format df (already sorted)
    gene_ranks = {
            'Gene': out_gene_list_s,
            'Rank': out_rank_list_s
        }
    gene_ranks_df = pd.DataFrame(gene_ranks)

    # run prerank 
    gsea_results_raw = gp.prerank(
        rnk = gene_ranks_df, 
        gene_sets = pathway_dict, 
        min_size = 4,
        seed = 1968
        )
    # filter output and append container to reutrn
    output = []
    for term in gsea_results_raw.results:
        print('looking at - ' + term.split('+')[0])
        tmp_out = [
            term.split('+')[0],
            db,
            term.split('+')[1],
            gsea_results_raw.results[term]['es'],
            gsea_results_raw.results[term]['nes'],
            gsea_results_raw.results[term]['pval'],
            gsea_results_raw.results[term]['fdr'],
            gsea_results_raw.results[term]['fwerp'],
            gsea_results_raw.results[term]['tag %'],
            gsea_results_raw.results[term]['gene %'],
            gsea_results_raw.results[term]['lead_genes'],
            gsea_results_raw.results[term]['matched_genes'],
        ]
        output.append(tmp_out)
    
    # | {
    # |  path id: pathway ID,
    # |  db: database name
    # |  path name: pathway name/description 
    # |  es: enrichment score,
    # |  nes: normalized enrichment score,
    # |  pval:  Nominal p-value (from the null distribution of the gene set,
    # |  fdr: FDR qvalue (adjusted False Discory Rate),
    # |  fwerp: Family wise error rate p-values,
    # |  tag %: Percent of gene set before running enrichment peak (ES),
    # |  gene %: Percent of gene list before running enrichment peak (ES),
    # |  lead_genes: leading edge genes (gene hits before running enrichment peak),
    # |  matched genes: genes matched to the data,
    # | }

    return output


# @shared_task
# def gsea_each_path(description, gene_in_path, out_gene_list, out_rank_list):

#     # output container
#     out = []

#     # format df (already sorted)
#     gene_ranks = {
#             'Gene': out_gene_list,
#             'Rank': out_rank_list
#         }
#     gene_ranks_df = pd.DataFrame(gene_ranks)

#     # print(gene_ranks_df.head)

#     # preprare user costumized gene set
#     user_set = {description: gene_in_path}

#     try:
#         gsea_res = gp.prerank(rnk = gene_ranks_df, gene_sets = user_set, seed = 1968)

#     except KeyError:
#         return out

#     return out
