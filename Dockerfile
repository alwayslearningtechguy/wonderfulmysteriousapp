# ============================
# Stage 1 — Test Stage
# ============================
FROM python:3.11-slim AS test-stage

WORKDIR /app
COPY . .

# Install runtime + test dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Run ONLY unit + integration tests
RUN pytest tests/unit tests/integration --maxfail=1 --disable-warnings -v


# ============================
# Stage 2 — Runtime Image
# ============================
FROM python:3.11-slim AS runtime

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
