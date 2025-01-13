FROM python:3.12-slim

WORKDIR /app

# Install dependencies for pyodbc
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc \
    unixodbc-dev \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 4000
CMD ["python", "api.py"]
