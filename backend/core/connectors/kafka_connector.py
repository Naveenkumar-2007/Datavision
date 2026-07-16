import asyncio
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from .base import LiveConnector

class KafkaConnector(LiveConnector):
    async def get_metrics_stream(self):
        while True:
            try:
                # We would connect to the Kafka broker at self.host
                topic = self.database_name if hasattr(self, 'database_name') and self.database_name else "live_sensor_data"
                consumer = AIOKafkaConsumer(
                    topic,
                    bootstrap_servers=self.host,
                    group_id="datavision-group",
                    auto_offset_reset="latest" # We only care about new live data
                )
                
                await consumer.start()
                try:
                    total_rows = 0
                    start_time = datetime.utcnow()
                    
                    # Fetch loop
                    while True:
                        # Wait for a batch of messages
                        result = await consumer.getmany(timeout_ms=1000)
                        
                        batch_count = sum(len(messages) for messages in result.values())
                        total_rows += batch_count
                        
                        now = datetime.utcnow()
                        delta_sec = (now - start_time).total_seconds()
                        rows_per_sec = total_rows / delta_sec if delta_sec > 0 else 0
                        
                        yield {
                            "timestamp": now.isoformat(),
                            "total_rows": total_rows,
                            "rows_per_sec": rows_per_sec,
                            "cpu_usage": 10.5,
                            "error_rate": 0.0,
                            "connector_source": "Kafka",
                            "status": "Healthy"
                        }
                        
                        await asyncio.sleep(1) # Send UI updates every 1 second
                        
                finally:
                    await consumer.stop()
                
            except Exception as e:
                print(f"Kafka Connection Error: {e}")
                yield {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_rows": 0,
                    "rows_per_sec": 0,
                    "cpu_usage": 0.0,
                    "error_rate": 100.0,
                    "connector_source": "Kafka",
                    "status": f"Connection Failed: {str(e)}"
                }
                await asyncio.sleep(5)
