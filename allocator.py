def compute_cost(split, venues, order_size, lambda_over, lambda_under, theta_queue):
    executed = 0
    cash_spent = 0.0

    for i in range(len(venues)):
        exe = min(split[i], venues[i]['ask_size'])
        executed += exe
        cash_spent += exe * (venues[i]['ask'] + venues[i].get('fee', 0))
        rebate = max(split[i] - exe, 0) * venues[i].get('rebate', 0)
        cash_spent -= rebate

    underfill = max(order_size - executed, 0)
    overfill = max(executed - order_size, 0)

    cost_penalty = lambda_under * underfill + lambda_over * overfill
    risk_penalty = theta_queue * (underfill + overfill)

    return cash_spent + cost_penalty + risk_penalty

def allocate(order_size, venues, lambda_over, lambda_under, theta_queue):
    step = 100
    N = len(venues)
    splits = [[]]

    for v in range(N):
        new_splits = []
        for alloc in splits:
            used = sum(alloc)
            max_v = min(order_size - used, venues[v]['ask_size'])
            for q in range(0, max_v + 1, step):
                new_splits.append(alloc + [q])
        splits = new_splits

    best_cost = float('inf')
    best_split = None
