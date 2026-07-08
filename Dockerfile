# syntax=docker/dockerfile:1

# ---- Builder stage -------------------------------------------------------
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

# Build wheels into an isolated prefix for a clean copy into the runtime image.
RUN python -m pip install --upgrade pip build \
    && pip install --prefix=/install .

# ---- Runtime stage -------------------------------------------------------
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MLOPS_HOST=0.0.0.0 \
    MLOPS_PORT=8000

# Create a non-root user to run the service.
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY src ./src

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

CMD ["uvicorn", "mlops_platform.main:app", "--host", "0.0.0.0", "--port", "8000"]
