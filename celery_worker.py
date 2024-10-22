import asyncio
from celery import Celery
from aiosmtplib import SMTP
from email.mime.text import MIMEText
from email.header import Header
from settings import settings
import traceback
from logger import get_logger
import os

app = Celery(__name__, broker=os.environ['CELERY_BROKER_URL'], backend=os.environ['CELERY_RESULT_BACKEND'])
logger = get_logger('celery_worker.log')


async def send_email_async(to_email, subject, body):
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = Header(settings.gmail_user, 'utf-8')
        msg['To'] = Header(to_email, 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        message = msg.as_string()
        async with SMTP(hostname=settings.smtp_server, port=settings.smtp_port) as smtp:
            await smtp.login(settings.gmail_user, settings.gmail_password)
            await smtp.sendmail(settings.gmail_user, to_email, message)
            logger.info(f"Email sent to {to_email}")
    except Exception as e:
        logger.error(f"Impossible sent message to {to_email}, reason <{str(e)}>")


@app.task
def send_email(subject, recipient, body):
    asyncio.run(send_email_async(subject, recipient, body))