from __future__ import annotations

import redis
from rq import Queue

from app.core.config import settings


redis_conn = redis.from_url(settings.redis_url)
WEBHOOK_QUEUE_NAME = "webhooks"
webhook_queue = Queue(WEBHOOK_QUEUE_NAME, connection=redis_conn)
