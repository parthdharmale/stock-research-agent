import json
import asyncio
import pika
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep the connection alive, but we don't expect to receive messages from the client
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

def consume_events_from_rabbitmq():
    """Runs in a background thread, listens to RabbitMQ, and triggers WebSocket broadcasts."""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    params = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='research_events_queue', durable=True)

    def callback(ch, method, properties, body):
        event_data = body.decode('utf-8')
        print(f"Broadcasting event to {len(active_connections)} clients...")

        loop = asyncio.new_event_loop()
        for connection in active_connections:
            asyncio.run_coroutine_threadsafe(connection.send_text(event_data), loop)

        ch.basic_ack(delivery_tag = method.delivery_tag)

    channel.basic_consume(queue='research_events_queue', on_message_callback=callback)
    channel.start_consuming()

@app.on_event("startup")
async def startup_event():
    """Starts the RabbitMQ consumer in a separate thread when the FastAPI app starts."""
    thread = Thread(target=consume_events_from_rabbitmq, daemon=True)
    thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("websocket_server:app", host="0.0.0.0", port=8000, reload=True)
              