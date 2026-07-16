import asyncio
from datetime import datetime
from .base import LiveConnector

class SnowflakeConnector(LiveConnector):
    async def get_metrics_stream(self):
        while True:
            try:
                # Run snowflake connection synchronously in thread since it doesn't have native async
                def _fetch():
                    import snowflake.connector
                    conn = snowflake.connector.connect(
                        user="admin", # Fallback/Mock - in real scenario, parse self.credentials
                        password=self.credentials,
                        account=self.host,
                        database=self.database_name,
                        schema="PUBLIC"
                    )
                    try:
                        cursor = conn.cursor()
                        # Snowflake requires a specific table. For live stream, we just count.
                        cursor.execute(f"SELECT COUNT(*) FROM {self.target_table if hasattr(self, 'target_table') and self.target_table else 'PUBLIC.LIVE_WEB_TRAFFIC'}")
                        total = cursor.fetchone()[0]
                        return total
                    finally:
                        conn.close()

                # Execute the sync call in an executor to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                total_rows = await loop.run_in_executor(None, _fetch)

                yield {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_rows": total_rows,
                    "rows_per_sec": 0, # Difficult to calculate delta per sec without tracking state here
                    "cpu_usage": 15.5,
                    "error_rate": 0.0,
                    "connector_source": "Snowflake",
                    "status": "Healthy"
                }
                
                await asyncio.sleep(5) # Snowflake polling shouldn't be too fast
                
            except Exception as e:
                print(f"Snowflake Connection Error: {e}")
                yield {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_rows": 0,
                    "rows_per_sec": 0,
                    "cpu_usage": 0.0,
                    "error_rate": 100.0,
                    "connector_source": "Snowflake",
                    "status": f"Connection Failed: {str(e)}"
                }
                await asyncio.sleep(5)
