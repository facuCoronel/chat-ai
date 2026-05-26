FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY pyproject.toml .
COPY app ./app
RUN pip install --no-cache-dir .

COPY . .
RUN chmod +x ./start.sh

CMD ["./start.sh"]
