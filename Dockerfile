# Use a lightweight Python image
FROM python:3.11-slim

WORKDIR /app

COPY . .

# Install app dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install test dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio httpx anyio

# Make sure Python can find the app package
ENV PYTHONPATH=/app

# Run tests during build (fail build if tests fail)
RUN pytest --maxfail=1 --disable-warnings

# Start the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
