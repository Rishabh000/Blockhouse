import json
from kafka import KafkaConsumer
from allocator import allocate

ORDER_SIZE = 5000
BOOTSTRAP_SERVERS = ['localhost:9092']  # Update if needed

# Initial unfilled order state
unfilled_shares = ORDER_SIZE
total_cash = 0.0
executed = 0

# Parameter config (can be looped over in backtest)
lambda_over = 0.4
lambda_under = 0.6
theta_queue = 0.3

consumer = KafkaConsumer(
    'mock_l1_stream',
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=False
)

venue_snapshots = {}

for msg in consumer:
    snap = msg.value
    ts = snap['ts_event']
    venue_id = snap['publisher_id']

    # Aggregate all venues for the current timestamp
    venue_snapshots[venue_id] = {
        'ask': float(snap['ask_px_00']),
        'ask_size': int(snap['ask_sz_00']),
        'fee': 0.0,
        'rebate': 0.0
    }

    # Once all venue data is collected (simplified as 3 venues for example)
    if len(venue_snapshots) == 3:  # Adjust based on dataset
        venues = list(venue_snapshots.values())

        alloc, cost = allocate(unfilled_shares, venues, lambda_over, lambda_under, theta_queue)

        fill = sum(min(alloc[i], venues[i]['ask_size']) for i in range(len(alloc)))
	cash = sum(min(alloc[i], venues[i]['ask_size']) * venues[i]['ask'] for i in range(len(alloc)))

        total_cash += cash
        executed += fill
        unfilled_shares -= fill

        print(f"Snapshot @ {ts} | Filled: {fill}, Remaining: {unfilled_shares}")

        venue_snapshots.clear()

        if unfilled_shares <= 0:
            print(f"\n Order fully executed.")
            print(f"Total Cash Spent: {total_cash:.2f}")
            print(f"Avg Fill Price: {total_cash / ORDER_SIZE:.4f}")
            break