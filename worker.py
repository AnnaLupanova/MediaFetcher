import asyncio
import aio_pika
from aiosmtplib import SMTP
from email.mime.text import MIMEText
from email.header import Header
from settings import settings, RABBITMQ_URL
import json
from logger import logger


async def send_email(to_email, subject, body):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = Header(settings.gmail_user, 'utf-8')
    msg['To'] = Header(to_email, 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    message = msg.as_string()
    async with SMTP(hostname=settings.smtp_server, port=settings.smtp_port) as smtp:
        await smtp.login(settings.gmail_user, settings.gmail_password)
        await smtp.sendmail(settings.gmail_user, to_email, message)
        logger.info(f"Email sent to {to_email}")


async def callback(message: aio_pika.IncomingMessage):
    async with message.process():
        decoded_message = json.loads(message.body.decode())
        try:
            to_email = decoded_message["recipient"]
            subject = decoded_message["subject"]
            body = decoded_message["body"]
            await send_email(to_email, subject, body)
        except ValueError as e:
            logger.error(f"Invalid message format. Reason <{str(e)}>")


async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue('email_queue')
        await queue.consume(callback)
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())