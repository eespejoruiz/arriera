FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
# OCR local (DATOS DEMO y modo local): español, inglés y portugués. Fuente para la capa de texto del PDF.
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng tesseract-ocr-por fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 arriera
COPY pyproject.toml ./
COPY arriera ./arriera
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir .
USER arriera
EXPOSE 8000
# Migra la base al arrancar y luego sirve la API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn arriera.main:app --host 0.0.0.0 --port 8000 --proxy-headers"]
