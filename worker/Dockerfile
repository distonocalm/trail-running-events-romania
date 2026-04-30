FROM python:3.12-slim

WORKDIR /app

COPY shared/ /app/shared/
RUN pip install --no-cache-dir /app/shared/

COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

COPY worker/ /app/worker/

WORKDIR /app/worker

CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=2"]
