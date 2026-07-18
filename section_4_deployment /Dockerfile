# Use a lightweight Python base image
FROM python:3.10-slim

WORKDIR /app

# Install FastAPI, Uvicorn, and llama-cpp-python
# We force the pre-compiled CPU wheel to avoid a 10-minute C++ build inside Docker
RUN pip install --no-cache-dir fastapi uvicorn requests \
    && pip install --no-cache-dir llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# Copy the model and the app code
COPY model.gguf .
COPY app.py .

# Expose the port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
