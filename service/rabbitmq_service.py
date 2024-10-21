import json
import aio_pika
from settings import settings, RABBITMQ_URL


async def get_rabbit_connection():
    return await aio_pika.connect_robust(RABBITMQ_URL)


async def publish_message(url: str, user_email: str):
    connection = await get_rabbit_connection()
    async with connection:
        channel = await connection.channel()
        message = {
            "recipient": user_email,
            "subject": "Ссылка на скачивание видео",
            "body": f"Ссылка на скачивание вашего видео: {url}",
            "attempts": 1
        }
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key="email_queue",
        )