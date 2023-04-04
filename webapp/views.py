# from django.forms import Form
# from django import forms
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, HttpResponse
from django.conf import settings
from webapp import models
import io
import sys
import os
import base64
import itertools
import ssl
import certifi
import re
from urllib.request import urlopen


from operator import itemgetter
import pandas as pd
import numpy as np
import scipy.stats as stats
from pathlib import Path
from collections import defaultdict
from celery import shared_task, group

from webapp.myforms import My_idmap_Form, My_Loci_Form, My_ORA_Form, My_Loci_Aggreg_Form
from webapp.run_loci import loci_match_unit, handle_loci_long_request
from webapp.run_ora import ora_each_path, ora_each_db, handle_ora_long_request
from webapp.run_aggreg import handle_loci_aggreg_request
from webapp.push_s3 import push_s3
from webapp.process_results import process_results
from webapp.register_job import register_job

# from asgiref.sync import sync_to_async
# import asyncio


# Create your views here.

# show info

def show_info(request):
    return render(request, 'index.html')

# show contact


def show_contacts(request):
    return render(request, 'contacts.html')

@csrf_exempt
def id_map(request):
    if request.method == 'POST':
        user_email = ''
        # paramters
        cur_species = request.POST.get('species')
        cur_type = request.POST.get('gene_type')

        print('cur_species - ', cur_species)
        print('cur_type - ', cur_type)
        
        if len(request.FILES) > 0:
            cur_gene_list = []
            for line in request.FILES['input_id_file']:
                cur_gene_list.append(line.decode().strip())
        else:
            cur_gene_list = request.POST.get('input_gene_list').split('\r\n')

        print('cur_gene_list- ', cur_gene_list)

        if len(cur_gene_list[-1]) == 0:
            cur_gene_list = cur_gene_list[:-1]
        
        print('cur_gene_list- ', cur_gene_list)
        
        # register job
        jobid = register_job(user_email, cur_species, cur_type, cur_gene_list)
            
        # condition check and return queryset
        if cur_type == 'ens':
            queryset = models.ID_Mapper.objects.select_related(
                    'species'
                ).filter(
                    species__name_short = cur_species
                ).filter(
                    gene_id__in = set(cur_gene_list)
                )
        else:
            queryset = models.ID_Mapper.objects.filter(entrez_id__in=set([str(x) for x in cur_gene_list]))
        missing_item_count = 0

        # check missing
        if len(queryset) < len(cur_gene_list):
            missing_item_count = len(cur_gene_list) - len(queryset)

        # save to s3
        target_url = push_s3(
            list(queryset.values()),
            ['id', 'Species', 'Ensembl Id', 'Ensembl Symbol', 'Entrez ID', 'NCBI Symbol','VGNC ID', 'VGNC Symbol', 'HGNC Orthologs', 'Human Ensembl ID', 'Human Entrez ID', 'HGNC Symbol'],
            jobid, '')
        # target_url = 'some test url'
        print(list(queryset.values()))
        return render(request, 'idmap_out.html', {'queryset': queryset, 'missing_count': [missing_item_count], 'target_url': target_url})

    if request.method == 'GET':
        form = My_idmap_Form()
        return render(request, 'idmap.html', {'form': form})

@csrf_exempt
def loci_match(request):
    if request.method == 'POST':
        # handle_loci_file()
        output = []
        long_running_thres = 100
        err_message = 'INVALID FORMAT. PLEASE DOUBLE CHECK.'
        no_email_message = 'You have submitted a potential long-running job. \n Please provide you email address.'
        #
        cur_species = request.POST.getlist('species')[0]
        cur_feature_list = request.POST.getlist('input_features')
        cur_cfeature_list = request.POST.getlist('computed_features')
        user_email = request.POST.getlist('email')
        
        #
        if len(request.FILES) > 0:
            cur_loci_list = []
            for line in request.FILES['input_loci_file']:
                cur_loci_list.append(line.decode())
        else:
            cur_loci_list = request.POST.get('input_loci_list').rstrip().split('\r\n')

        
        if len(cur_loci_list[-1]) == 0:
            cur_loci_list = cur_loci_list[:-1]

        # reject long input
        if user_email[0] == '' and len(cur_loci_list) >= long_running_thres:
            return render(request, 'long_running_reminder.html')

        # append short intron
        if 'intron' in cur_cfeature_list:
            cur_cfeature_list.append('short intron')

        #####
        cur_chr_list = []
        cur_coord_list = []

        for item in cur_loci_list:
            try:
                cur_chr_list.append(item.split(':')[0])
                cur_coord_list.append(int(item.split(':')[1]))
            except:
                return render(request, 'loci.html', {'err': err_message})

        # check different length
        if len(cur_chr_list) != len(cur_coord_list):
            return render(request, 'loci.html', {'err': err_message})

        
        # register job
        
        jobid = register_job(user_email, cur_species, cur_feature_list.extend(cur_cfeature_list), cur_loci_list)
        
        # check size
        if len(cur_loci_list) < long_running_thres:
            # solo - sync way
            # start_time = time.time()
            # print('run short loci')
            for (cur_chr, cur_loci) in itertools.zip_longest(cur_chr_list, cur_coord_list):
                out_tmp = loci_match_unit(cur_species, cur_feature_list, cur_cfeature_list, cur_chr, cur_loci)
                output.extend(out_tmp)
            # print("solo --- %s seconds ---" % (time.time() - start_time))
            #
            target_url = push_s3(
                output,
                ['Chromosome', 'Coordinates', 'Feature', 'Description', 'Transcript_id ID', 'Ensembl Gene ID', 'Gene Biotype', 'Strand'],
                jobid, '')
            return render(request, 'loci_out.html', {'output': output, 'target_url': target_url})
        else:
            # parallel - async way
            # print('ready to handle_loci_long_request')
            handle_loci_long_request.delay(cur_species, cur_feature_list, cur_cfeature_list, cur_chr_list, cur_coord_list, jobid, user_email[0])
            # print('done handle_loci_long_request')
            return render(request, 'loci_out_async.html', {'jobid': jobid, 'user_email': user_email[0]})

    if request.method == 'GET':
        form = My_Loci_Form()
        return render(request, 'loci.html', {'form': form})

@csrf_exempt
def loci_aggreg(request):
    if request.method == 'POST':
        # handle_loci_file()
        output = []
        long_running_thres = 100
        err_message = 'INVALID FORMAT. PLEASE DOUBLE CHECK.'
        no_email_message = 'You have submitted a potential long-running job. \n Please provide you email address.'
        #
        cur_species = request.POST.getlist('species')[0]
        cur_loci_list = request.POST.getlist('input_loci_list')
        cur_methods_list = request.POST.getlist('input_methods_list')
        user_email = request.POST.getlist('email')

        #
        if len(request.FILES) > 0:
            cur_loci_list = []
            for line in request.FILES['input_loci_file']:
                cur_loci_list.append(line.decode())
        else:
            cur_loci_list = request.POST.get('input_loci_list').rstrip().split('\r\n')

        # print(cur_loci_list)
        
        if len(cur_loci_list[-1]) == 0:
            cur_loci_list = cur_loci_list[:-1]

        # print(cur_loci_list)

        # reject long input
        if user_email[0] == '' and len(cur_loci_list) >= long_running_thres:
            return render(request, 'long_running_reminder.html')

        # #####
        cur_chr_list = []
        cur_coord_list = []
        cur_pval_list = []

        for item in cur_loci_list:
            try:
                tmp = re.split(':|,',item)
                cur_chr_list.append(tmp[0])
                cur_coord_list.append(int(tmp[1]))
                cur_pval_list.append(float(tmp[2]))
            except:
                return render(request, 'loci_aggreg.html', {'err': err_message})
        
        # print(cur_chr_list)
        # print(cur_coord_list)
        # print(cur_pval_list)

        # check different length
        if not (len(cur_chr_list) == len(cur_coord_list) == len(cur_pval_list)):
            return render(request, 'loci_aggreg.html', {'err': err_message})


        # register job
        jobid = register_job(user_email, cur_species, cur_methods_list, cur_loci_list)

        # parallel - async way
        # print('ready to handle_loci_long_request')
        handle_loci_aggreg_request.delay(cur_species, cur_methods_list, cur_chr_list, cur_coord_list, cur_pval_list, jobid, user_email[0])
        
        # print('done handle_loci_long_request')
        return render(request, 'loci_aggreg_out_async.html', {'jobid': jobid, 'user_email': user_email[0]})

    if request.method == 'GET':
        form = My_Loci_Aggreg_Form()
        return render(request, 'loci_aggreg.html', {'form': form})

@csrf_exempt
def run_ora(request):
    template = 'ora.html'
    if request.method == 'POST':
        print('received post ')
        
        err_message = 'INVALID FORMAT. PLEASE DOUBLE CHECK.'
        no_email_message = 'You have submitted a potential long-running job. \n Please provide you email address.'

        cur_species = request.POST.get('species')
        cur_db_list = request.POST.getlist('input_db_list')
        user_email = request.POST.getlist('email')

        if len(request.FILES) > 0:
            cur_gene_list = []
            for line in request.FILES['input_gene_file']:
                cur_gene_list.append(line.decode().strip())
        else:
            cur_gene_list = request.POST.get('input_gene_list').rstrip().split('\r\n')

        if len(cur_gene_list) == 0:
            cur_gene_list = cur_gene_list[:-1]

        # reject long input
        if (len(cur_db_list) > 1 or 'msigdb' in cur_db_list) and user_email[0] == '':
            return render(request, 'long_running_reminder.html')

        # process input gene list
        sig_gene = []
        total_gene = []
        for item in cur_gene_list:
            try:
                tmp_gene_id = item.split(',')[0]
                tmp_gene_sig = int(item.split(',')[1])
            except Exception:
                return render(request, template, {'err': err_message})
            #
            total_gene.append(tmp_gene_id)
            if int(tmp_gene_sig) == 1:
                sig_gene.append(tmp_gene_id)
            # dedup
            sig_gene = list(set(sig_gene))
            total_gene = list(set(total_gene))

        output_all = []
        
        # print('cur_db_list ', cur_db_list)

        # register job
        jobid = register_job(user_email[0], cur_species, cur_db_list, cur_gene_list)

        # deal with input
        if len(cur_db_list) == 1 and 'msigdb' not in cur_db_list: # 

            output_all = ora_each_db(cur_species, cur_db_list[0], sig_gene, total_gene)
            target_url = push_s3(
                output_all,
                ['Term ID', 'Source', 'Term Description', 'DB_Loss Total', 'DB_Loss Sig', 'Sig Gene Count', 'Total Gene Count', 'Hit Percentage', 'P value', 'Hit Gene List'],
                jobid, '')
            return render(request, 'ora_out.html', {'output': output_all, 'target_url': target_url})

        else:
            out = handle_ora_long_request.delay(cur_db_list, cur_species, sig_gene, total_gene, jobid, user_email[0])

            # print('seeking id from main ', out.id)
            
            return render(request, 'ora_out_async.html', {'jobid': jobid, 'user_email': user_email[0]})

    if request.method == 'GET':
        form = My_ORA_Form()
        return render(request, template, {'form': form})

@csrf_exempt
def run_gsea(request):
    template = 'ora.html'
    if request.method == 'POST':
        print('received post ')
        
        err_message = 'INVALID FORMAT. PLEASE DOUBLE CHECK.'
        no_email_message = 'You have submitted a potential long-running job. \n Please provide you email address.'

        cur_species = request.POST.get('species')
        cur_db_list = request.POST.getlist('input_db_list')
        user_email = request.POST.getlist('email')

        if len(request.FILES) > 0:
            cur_gene_list = []
            for line in request.FILES['input_gene_file']:
                cur_gene_list.append(line.decode().strip())
        else:
            cur_gene_list = request.POST.get('input_gene_list').rstrip().split('\r\n')

        if len(cur_gene_list) == 0:
            cur_gene_list = cur_gene_list[:-1]

        # reject long input
        if (len(cur_db_list) > 1 or 'msigdb' in cur_db_list) and user_email[0] == '':
            return render(request, 'long_running_reminder.html')

        # process input gene list
        sig_gene = []
        total_gene = []
        for item in cur_gene_list:
            try:
                tmp_gene_id = item.split(',')[0]
                tmp_gene_sig = int(item.split(',')[1])
            except Exception:
                return render(request, template, {'err': err_message})
            #
            total_gene.append(tmp_gene_id)
            if int(tmp_gene_sig) == 1:
                sig_gene.append(tmp_gene_id)
            # dedup
            sig_gene = list(set(sig_gene))
            total_gene = list(set(total_gene))

        output_all = []
        
        # print('cur_db_list ', cur_db_list)

        # register job
        jobid = register_job(user_email[0], cur_species, cur_db_list, cur_gene_list)

        # deal with input
        if len(cur_db_list) == 1 and 'msigdb' not in cur_db_list: # 

            output_all = ora_each_db(cur_species, cur_db_list[0], sig_gene, total_gene)
            target_url = push_s3(
                output_all,
                ['Term ID', 'Source', 'Term Description', 'DB_Loss Total', 'DB_Loss Sig', 'Sig Gene Count', 'Total Gene Count', 'Hit Percentage', 'P value', 'Hit Gene List'],
                jobid, '')
            return render(request, 'ora_out.html', {'output': output_all, 'target_url': target_url})

        else:
            out = handle_ora_long_request.delay(cur_db_list, cur_species, sig_gene, total_gene, jobid, user_email[0])

            # print('seeking id from main ', out.id)
            
            return render(request, 'ora_out_async.html', {'jobid': jobid, 'user_email': user_email[0]})

    if request.method == 'GET':
        form = My_ORA_Form()
        return render(request, template, {'form': form})


def show_results(request):
    if request.method == 'GET':
        tmp_jobid = request.GET.get('jobid')
        job_obj = models.Task.objects.filter(jobid=tmp_jobid)

        if job_obj.exists():
            tmp_url = list(job_obj.values('url'))[0]['url']
        else:
            return render(request, '404.html')

        ssl._create_default_https_context = ssl._create_unverified_context

        streamed_file = urlopen(tmp_url)

        results = []
        for i, line in enumerate(streamed_file):
            tmp = line.decode('utf8').rstrip().split('\t')[0].split(',')
            results.append(tmp)

        header, processed_results, did_cut = process_results(results)

        if len(results[0]) == 10:
            return render(request, 'show_results_ora.html', {'header': header, 'output': processed_results, 'target_url': tmp_url,'did_cut': did_cut})
        else:
            return render(request, 'show_results_loci.html', {'header': header, 'output': processed_results, 'target_url': tmp_url,'did_cut': did_cut})
