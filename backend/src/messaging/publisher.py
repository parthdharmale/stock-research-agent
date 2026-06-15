import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

def publish_event(event_data: dict):
    """Publishes an event or final report to the RabbitMQ events queue."""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    try:
        # Establish a connection
        params = pika.URLParameters(rabbitmq_url)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Ensure the queue exists
        channel.queue_declare(queue='research_events_queue', durable=True)

        #Publish the message
        channel.basic_publish(
            exchange='',
            routing_key='research_events_queue',
            body=json.dumps(event_data),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        connection.close()
    except Exception as e:
        print(f"Failed to publish event: {e}")