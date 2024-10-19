import asyncio
import aio_pika
from aiosmtplib import SMTP


async def main():
    connection = await aio_pika.connect_robust("amqp://localhost/")
    async with connection:
        channel = await connection.channel()

        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue('email_queue')

if __name__ == '__main__':
    asyncio.run(main())
