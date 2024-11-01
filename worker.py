import asyncio
from aio_pika import connect_robust, IncomingMessage, Message
from aiosmtplib import SMTP
from email.mime.text import MIMEText
from email.header import Header
from settings import settings
import json
import logging
from logging.handlers import TimedRotatingFileHandler


logger = logging.getLogger(__name__)
_log_format = f"%(asctime)s - [%(levelname)s] - %(filename)s - %(message)s"
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler("worker.log", when='midnight', backupCount=10)
handler.setFormatter(logging.Formatter(_log_format))
logger.addHandler(handler)
QUEUE_NAME = "email_queue"
DEAD_LETTER_QUEUE = "email_ttl_queue"
MESSAGE_TTL = 1000
DEAD_LETTER_EXCHANGE = "dlx"
MAX_RETRIES = 3
dead_letter_args = {
            "x-message-ttl": MESSAGE_TTL,
            "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE
        }

async def send_email(to_email, subject, body):#
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
        raise


async def on_message(message: IncomingMessage):
    async with message.process(ignore_processed=True):
        try:
            body = json.loads(message.body)
            recipient = body["recipient"]
            subject = body["subject"]
            body_content = body["body"]
            await send_email(recipient, subject, body_content)
            await message.ack()
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            connection = await connect_robust(settings.rabbitmq_url)
            async with connection:
                channel = await connection.channel()
                await channel.default_exchange.publish(
                    message, routing_key=DEAD_LETTER_QUEUE
                )
                logger.info("Message sent to dead letter queue")


async def main():
    connection = await connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue(QUEUE_NAME)
        await queue.consume(on_message)
        dead_letter_queue = await channel.declare_queue(DEAD_LETTER_QUEUE, durable=True, arguments=dead_letter_args)
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())