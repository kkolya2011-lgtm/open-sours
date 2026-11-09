import time
from collections import defaultdict, deque

_hits: dict[int, deque] = defaultdict(deque)

def allow(user_id: int, limit: int, window: int = 60) -> bool:
    now = time.time()
    dq = _hits[user_id]
    while dq and now - dq[0] > window:
        dq.popleft()
    if not dq:
        _hits.pop(user_id, None)
        dq = _hits[user_id]
    if len(dq) >= limit:
        return False
    dq.append(now)
    return True
