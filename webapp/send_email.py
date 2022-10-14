from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import datetime
import os


@shared_task
def send_email(user_email, type, jobid=None, view_link=None, download_link=None):
    if type == 'init':
        send_mail(
            '[EnrichKit] Job Initiated',
            render_to_string(os.path.join(os.getcwd(), 'webapp/templates/email_msg_init.txt'), {'time': datetime.now().strftime("%m/%d/%Y %H:%M:%S"), 'jobid': jobid}),
            'enrichkit.info@gmail.com',
            [user_email])
    elif type == 'finish':
        send_mail(
            '[EnrichKit] Job Finished',
            render_to_string(os.path.join(os.getcwd(), 'webapp/templates/email_msg_finish.txt'), {'view_link': view_link, 'download_link': download_link}),
            'enrichkit.info@gmail.com',
            [user_email])
    return True
