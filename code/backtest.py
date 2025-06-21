import json
import pandas as pd
from allocator import allocate

ORDER_SIZE = 5000
CHUNK_SIZE = 100

# Load market data
df = pd.read_csv('l1_day.csv')
df = df[df['ts_event'].between('13:36:32', '13:45:14')]

# Format timestamp if needed
df['ts_event'] = pd.to_datetime(df['ts_event'])

# Parameters to search
lambdas_over = [0.2, 0.4, 0.6]
lambdas_under = [0.2, 0.4, 0.6]
thetas = [0.1, 0.3, 0.5]

# Group snapshots by timestamp
grouped = df.groupby('ts_event')

def run_allocator(df_group, lam_o, lam_u, theta):
    unfilled = ORDER_SIZE
    total_cash = 0.0

    for _, snap_df in df_group:
        venues = []
        for _, row in snap_df.iterrows():
            venues.append({
                'ask': float(row['ask_px_00']),
                'ask_size': int(row['ask_sz_00']),
                'fee': 0.0,
                'rebate': 0.0
            })

        alloc, _ = allocate(unfilled, venues, lam_o, lam_u, theta)

        fill = sum(min(alloc[i], venues[i]['ask_size']) for i in range(len(alloc)))
        cash = sum(min(alloc[i], venues[i]['ask_size']) * venues[i]['ask'] for i in range(len(alloc)))

        total_cash += cash
        unfilled -= fill

        if unfilled <= 0:
            break
	return total_cash, ORDER_SIZE - unfilled

def run_best_ask(df_group):
    unfilled = ORDER_SIZE
    total_cash = 0.0

    for _, snap_df in df_group:
        best_row = snap_df.loc[snap_df['ask_px_00'].idxmin()]
        ask = best_row['ask_px_00']
        ask_size = best_row['ask_sz_00']
        fill = min(ask_size, unfilled)

        total_cash += fill * ask
        unfilled -= fill

        if unfilled <= 0:
            break

    return total_cash, ORDER_SIZE - unfilled

def run_twap(df, num_intervals=5):
    interval_length = (df['ts_event'].max() - df['ts_event'].min()) / num_intervals
    total_cash = 0.0
    unfilled = ORDER_SIZE
    df_sorted = df.sort_values('ts_event')

    for i in range(num_intervals):
        start = df_sorted['ts_event'].min() + i * interval_length
        end = start + interval_length
        chunk = df_sorted[(df_sorted['ts_event'] >= start) & (df_sorted['ts_event'] < end)]

        if chunk.empty:
            continue

        shares_to_buy = ORDER_SIZE // num_intervals
        venues = chunk.sort_values('ask_px_00')
        remaining = shares_to_buy

        for _, row in venues.iterrows():
            size = min(remaining, row['ask_sz_00'])
            total_cash += size * row['ask_px_00']
            remaining -= size
            if remaining <= 0:
                break

        unfilled -= (shares_to_buy - remaining)
        if unfilled <= 0:
		break

    return total_cash, ORDER_SIZE - unfilled

def run_vwap(df):
    total_cash = 0.0
    unfilled = ORDER_SIZE
    df_sorted = df.sort_values('ts_event')

    for ts, group in df_sorted.groupby('ts_event'):
        venues = group.copy()
        total_volume = venues['ask_sz_00'].sum()
        if total_volume == 0:
            continue

        for _, row in venues.iterrows():
            weight = row['ask_sz_00'] / total_volume
            target_shares = int(weight * unfilled)
            size = min(target_shares, row['ask_sz_00'])
            total_cash += size * row['ask_px_00']
            unfilled -= size
            if unfilled <= 0:
                break
        if unfilled <= 0:
            break

    return total_cash, ORDER_SIZE - unfilled


def compute_bps_savings(base_cash, opt_cash):

    if base_cash == 0:
        return 0.0
    return round((base_cash - opt_cash) / base_cash * 10000, 2)

# Run grid search
best_config = None
best_cash = float('inf')
best_fill = 0

grouped_data = list(grouped)

for lam_o in lambdas_over:
    for lam_u in lambdas_under:
        for theta in thetas:
            cash, filled = run_allocator(grouped_data, lam_o, lam_u, theta)

	    print(f"λo={lam_o}, λu={lam_u}, θ={theta} → Fill: {filled}, Cash: {cash:.2f}")

            if filled > best_fill or (filled == ORDER_SIZE and cash < best_cash):
                best_fill = filled
                best_cash = cash
                best_config = (lam_o, lam_u, theta)

if best_config is None:
    print("⚠️ No configuration filled the order. Using fallback values.")
    # Use arbitrary reasonable fallback (or based on intuition)
    lam_o, lam_u, theta = 0.4, 0.4, 0.3
else:
    lam_o, lam_u, theta = best_config


opt_cash, _ = run_allocator(grouped_data, lam_o, lam_u, theta)

# Baseline runs
best_ask_cash, _ = run_best_ask(grouped_data)
twap_cash, _ = run_twap(df)
vwap_cash, _ = run_vwap(df)

# Final output
result = {
    "best_parameters": {
        "lambda_over": lam_o,
        "lambda_under": lam_u,
        "theta_queue": theta
    },
    "optimized": {
        "total_cash": round(opt_cash, 2),
        "avg_fill_px": round(opt_cash / ORDER_SIZE, 4)
    },
    "baselines": {
    "best_ask": {
        "total_cash": round(best_ask_cash, 2),
        "avg_fill_px": round(best_ask_cash / ORDER_SIZE, 4)
    },
    "twap": {
        "total_cash": round(twap_cash, 2),
        "avg_fill_px": round(twap_cash / ORDER_SIZE, 4)
    },
    "vwap": {
        "total_cash": round(vwap_cash, 2),
        "avg_fill_px": round(vwap_cash / ORDER_SIZE, 4)
    }
},
"savings_vs_baselines_bps": {
    "best_ask": compute_bps_savings(best_ask_cash, opt_cash),
    "twap": compute_bps_savings(twap_cash, opt_cash),
    "vwap": compute_bps_savings(vwap_cash, opt_cash)
}

}

print(json.dumps(result, indent=2))
with open("output.json", "w") as f:
    json.dump(result, f, indent=2) 	
