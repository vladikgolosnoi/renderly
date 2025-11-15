from __future__ import annotations

from rq import Connection, Worker

from app.core.tasks import redis_conn, WEBHOOK_QUEUE_NAME


def main() -> None:
    with Connection(redis_conn):
        worker = Worker([WEBHOOK_QUEUE_NAME])
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
