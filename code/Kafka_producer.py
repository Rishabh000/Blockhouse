import pandas as pd
import json
import time
from datetime import datetime
from kafka import KafkaProducer

# --- Configuration ---
CSV_PATH = 'l1_day.csv'
TOPIC = 'mock_l1_stream'
BOOTSTRAP_SERVERS = ['localhost:9092']  # or EC2 IP if running remotely
TIME_FORMAT = "%H:%M:%S.%f"
SIMULATION_START = "13:36:32"
SIMULATION_END = "13:45:14"

# --- Kafka Setup ---
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# --- Load & Filter Data ---
df = pd.read_csv(CSV_PATH)
df['ts_event'] = pd.to_datetime(df['ts_event'])

# Filter time range
start_ts = df[df['ts_event'].dt.strftime('%H:%M:%S') >= SIMULATION_START]
end_ts = start_ts[start_ts['ts_event'].dt.strftime('%H:%M:%S') <= SIMULATION_END]
df_filtered = end_ts.sort_values('ts_event')

# --- Stream Snapshots ---
prev_ts = None
for ts, group in df_filtered.groupby('ts_event'):
    if prev_ts is not None:
        delta = (ts - prev_ts).total_seconds()
        time.sleep(min(delta, 1))  # Optional: cap sleep time to 1 sec for faster replay
    prev_ts = ts

    for _, row in group.iterrows():
        message = {
            'ts_event': ts.strftime(TIME_FORMAT)[:-3],  # trim microseconds
            'publisher_id': row['publisher_id'],
            'ask_px_00': row['ask_px_00'],
            'ask_sz_00': row['ask_sz_00']
        }
        producer.send(TOPIC, message)
        print(f"Sent: {message}")

producer.flush()
producer.close()