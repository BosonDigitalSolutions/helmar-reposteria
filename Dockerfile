FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements/base.txt requirements/prod.txt requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

COPY . .

EXPOSE 8000
