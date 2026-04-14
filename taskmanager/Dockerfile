# Using a lightweight Python image
FROM python:3.12-slim

# Prevents Python from generating .pyc files and enables real-time logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Working directory inside the container
WORKDIR /app

# Installs system dependencies necessary for MySQL and compilation
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Installs Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copies the remaining code
COPY . .

# Exposes the Django port
EXPOSE 8000