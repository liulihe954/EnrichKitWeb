import itertools
from webapp import models
from webapp.push_s3 import push_s3
import pandas as pd
import numpy as np
import scipy.stats as stats
from collections import defaultdict
from celery import shared_task, current_task, group
from celery.result import allow_join_result
import concurrent.futures

from webapp.send_email import send_email


@shared_task
def handle_ora_long_request(cur_db_list, cur_species, sig_gene, total_gene, jobid, user_email):
    # step 0 notification email
    send_email(user_email, type='init', jobid=jobid)

    output_all = []
    output_msigdb = []
    # firstly, do msigdb
    if 'msigdb' in cur_db_list:
        output_msigdb = ora_each_db(cur_species, 'msigdb', sig_gene, total_gene)

    # print('current_task.request.id - ', current_task.request.id)
    # print('msigdb_job id - ', msigdb_job.id)
    # output_msigdb = msigdb_job.get()


    # other 
    filter_db_list = [item for item in cur_db_list if item != 'msigdb']

    # step 1 do the job in parallel
    with allow_join_result():
        out_t = group(
            ora_each_db.s(cur_species, db, sig_gene, total_gene) for db in filter_db_list
        ).apply_async()
        out = out_t.get()
    children_list = [task for parents in out_t.children for task in parents.as_list()[::-1]]
    # print('others id  ', children_list)

    #
    output_all = list(itertools.chain.from_iterable(out))
    if len(output_msigdb) > 0:
        output_all.extend(output_msigdb)

    # if 'msigdb' in cur_db_list:
    #     out_msigdb = ora_each_db(cur_species, 'msigdb', sig_gene, total_gene)
    
    # output_all.extend(out_msigdb)
    # with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    #     future = [executor.submit(ora_each_db, cur_species, db, sig_gene, total_gene) for db in cur_db_list]
    # # collect output
    # for item in concurrent.futures.as_completed(future):
    #     output_all.extend(item.result())

    # gather list of worker ids
    children_list.append(current_task.request.id)

    # push to s3
    target_url = push_s3(
        output_all,
        ['Term ID', 'Source', 'Term Description', 'DB_Loss Total', 'DB_Loss Sig', 'Sig Gene Count', 'Total Gene Count', 'Hit Percentage', 'P value', 'Hit Gene List'],
        jobid, children_list)

    # step 3 send email
    view_link_concat = "http://enrichkit.info/results/?jobid=" + jobid

    send_email(user_email, type='finish', view_link=view_link_concat, download_link=target_url)

    return True


@shared_task
def ora_each_path(k, v, db, S, N, DB_Loss_total, DB_Loss_sig, total_gene, sig_gene):
    # print('check database ', db, ' pathway ', k[0])
    m = len(set(total_gene).intersection(v))
    if m > 4:
        findG = set(sig_gene).intersection(v)
        s = len(findG)
        cur_table = [[s, S - s], [m - s, N - m - S + s]]
        odd_ratio, p_value = stats.fisher_exact(cur_table)
        if k[1] and s > 2 and p_value < 1:
            cur_pathway_out = [
                k[0],
                db,
                k[1],
                DB_Loss_total,
                DB_Loss_sig,
                s,
                m,
                round(s / m, 2),
                round(p_value, 4),
                "/".join(findG)]
            return cur_pathway_out
    return []


@shared_task
def ora_each_db(cur_species, db, sig_gene, total_gene, type='main'):
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

    # del cur_db_expanded_df_raw
    # cur_db_expanded_df_raw.replace('', np.nan, inplace=True)
    # cur_db_expanded_df = cur_db_expanded_df_raw.dropna()

    all_db_gene_list = cur_db_expanded_df.ek_gene__gene_id.unique()
    # all_db_gene_list = [i for i in all_db_gene_list if i]
    
    N = len(set(total_gene).intersection(all_db_gene_list))
    S = len(set(sig_gene).intersection(all_db_gene_list))
    DB_Loss_total = (len(total_gene) - N) / len(total_gene)
    DB_Loss_sig = (len(sig_gene) - S) / len(sig_gene)

    del all_db_gene_list

    pathway_dict = defaultdict(list)
    cc = 0
    for index, result in cur_db_expanded_df.iterrows():
        cc += 1
        # if cc < 10:
        #     print(result)
        if len(result['ek_gene__gene_id']) >  0:
            pathway_dict[(result['ek_pathway__pathway_id'], result['ek_pathway__pathway_description'])].append(result['ek_gene__gene_id'])
        if cc % 10000 == 0:
            continue
            # print('processed %d' % cc)
    #
    if type == 'main':
        for k, v in pathway_dict.items():
            tmp = ora_each_path(k, v, db, S, N, DB_Loss_total, DB_Loss_sig, total_gene, sig_gene)
            if len(tmp) > 0:
                output.append(tmp)
    elif type == 'queue':
        with allow_join_result():
            out = group(
                ora_each_path.s(k, v, db, S, N, DB_Loss_total, DB_Loss_sig, total_gene, sig_gene) for k, v in pathway_dict.items()
            ).apply_async().get()
        #
        for item in out:
            if len(item) > 0:
                output.append(item)

    return output