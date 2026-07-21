FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev

COPY services ./services
RUN mkdir -p /app/services/maintenance_service/data/uploads

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "uvicorn", "services.maintenance_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
