FROM python:3.13-slim

# Instalamos uv para gestión de paquetes ultra-rápida
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo archivos de dependencias primero (mejor cache de Docker)
COPY pyproject.toml .
COPY requirements.txt .

# Forzar bcrypt 4.2.0 para evitar el error "password cannot be longer than 72 bytes"
# RUN uv pip install --system "bcrypt==4.2.0" "passlib>=1.7.4"

# Instalar dependencias en el sistema Python (sin entorno virtual)
RUN uv pip install --system -r requirements.txt

# Copiar el código de la aplicación
COPY . .


