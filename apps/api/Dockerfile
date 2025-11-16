FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    RUN_DB_MIGRATIONS=1

ARG DEBIAN_MIRROR="http://deb.debian.org/debian"
ARG DEBIAN_SECURITY_MIRROR="http://security.debian.org/debian-security"
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN set -eux; \
    sed -Ei "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}|g" /etc/apt/sources.list; \
    sed -Ei "s|http://security.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" /etc/apt/sources.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends build-essential; \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
COPY migrations migrations
COPY alembic.ini .

COPY entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
