FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY services/messaging/pyproject.toml ./pyproject.toml
COPY services/messaging/app ./app
RUN pip install --no-cache-dir .

COPY services/messaging/alembic.ini ./alembic.ini
COPY services/messaging/alembic ./alembic
COPY services/messaging/start.sh ./start.sh
RUN chmod +x ./start.sh

CMD ["./start.sh"]
