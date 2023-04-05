import json
from webapp import models
from celery import shared_task
import uuid
from io import StringIO
import csv
from django.core.files.base import ContentFile

def register_job(user_email, species, options, content):
    jobid = str(uuid.uuid4())
    url = "https://enrichkit-web-storage.s3.amazonaws.com/input/" + jobid + ".txt"

    # to stringIO
    f = StringIO()
    f.write(json.dumps(content))
    
    str_data = f.getvalue().encode('utf8')

    # print('type of str_data - ', type(str_data))

    content_file = ContentFile(str_data, name=str(jobid + ".txt"))

    # print('type of content_file - ', type(content_file))

    f.close()

    tmp_task_obj = models.Task(
        jobid=jobid,
        user_email=user_email,
        status = 0,
        input_url = url,
        input_content = content_file,
        species=species,
        options=json.dumps(options))

    tmp_task_obj.save()
    return jobid

# jobid = models.CharField(verbose_name='unique id of each job received', max_length=100)
# time = models.DateTimeField(verbose_name='time of job received', auto_now_add=True)
# user_email = models.EmailField(verbose_name='user email', max_length=100, null=True)

# # input
# species = models.CharField(verbose_name='the species the user is working', max_length=10,null=True)
# options = models.CharField(verbose_name='the input parameters of the current job', max_length=10,null=True)
# content = models.CharField(verbose_name='the user-provided input list of the current job', max_length=10, null=True)