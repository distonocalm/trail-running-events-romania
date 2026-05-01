FROM python:3.12-slim

WORKDIR /app

COPY shared/ /app/shared/
RUN pip install --no-cache-dir /app/shared/

COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

COPY api/ /app/api/

WORKDIR /app/api

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
