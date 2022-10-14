from django.core.files.base import ContentFile
from webapp import models
import csv
import json
from io import StringIO


def push_s3(content_list, header_list, jobid, list_of_workers):
    # print('list_of_workers passed in -', list_of_workers)
    #
    url = "https://enrichkit-web-storage.s3.amazonaws.com/results/" + jobid + ".csv"

    # to stringIO
    f = StringIO()
    writer = csv.writer(f)
    writer.writerow(header_list)

    for item in content_list:
        if isinstance(item, list):
            writer.writerow(item)
        else:
            writer.writerow(item.values())
    
    str_data = f.getvalue().encode('utf8')

    content_file = ContentFile(str_data, name=str(jobid + ".csv"))

    # update task instance
    obj = models.Task.objects.filter(jobid=jobid).first()
    obj.url = url
    obj.status = 1
    obj.list_of_workers = json.dumps(list_of_workers)
    obj.csv.delete()
    obj.csv = content_file
    obj.save()
    return url
