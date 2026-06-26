import pika
import json
import os
from dotenv import load_dotenv

from src.core.graph import portfolio_app
from src.messaging.publisher import publish_event
from src.core.memory import memory_manager

load_dotenv()

def process_task(ch, method, properties, body):
    """Callback triggered when a new taskk arrives in the queue."""
    print("\n Received new research task from queue!")

    request_data = json.loads(body)
    tickers = request_data.get("tickers", [])
    task_requirements = request_data.get("task_requirements", "Provide a standard financial report")

    print(f"Target Tickers: {tickers}")

    initial_state = {
        "task_requirements": task_requirements,
        "tickers": tickers,
        "revision_count": 0,
        "feedback": "None"
    }

    thread_config = {"configurable": {"thread_id": f"task_{tickers[0]}"}}

    print("🤖 AI agents are now processing the task...\n")

    paused_state = portfolio_app.invoke(initial_state, config=thread_config)
    state_snapshot = portfolio_app.get_state(thread_config)

    if state_snapshot.next and state_snapshot.next[0] == 'report_writer':
        print("\n" + "="*50)
        print("🛑 HUMAN-IN-THE-LOOP BREAKPOINT TRIGGERED 🛑")
        print("Data has been gathered and analyzed. State frozen in checkpoints.sqlite.")
        print("="*50 + "\n")
        
        input("👨‍💼 [MANAGER]: Review the logs above. Press ENTER to authorize writing the final report...")
        
        print("✅ Authorized. Resuming compilation from SQLite snapshot...")
        
        final_state = portfolio_app.invoke(None, config=thread_config)
    else:
        final_state = paused_state

    print("AI Processing completed.\n")

    final_report = final_state.get("final_report", "Error: No report generated.")

    if final_report and final_report != "None":
        print("🧠 Saving report to Vector Memory...")
        for ticker in tickers:
            memory_manager.save_report(ticker, final_report)

    publish_event({
        "status": "completed",
        "tickers": tickers,
        "report": final_report
    })

    print("Final report published to events queue.\n")

    ch.basic_ack(delivery_tag = method.delivery_tag)

def start_consumer():
    """Starts listening the RabbitMQ tasks queue."""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    params = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='research_tasks_queue', durable=True)

    print("Worker is listening for tasks on 'research_tasks_queue'...")
    channel.basic_consume(queue='research_tasks_queue', on_message_callback=process_task)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Stopping consumer...")
        channel.stop_consuming()
        connection.close()