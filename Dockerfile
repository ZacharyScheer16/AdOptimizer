FROM python:3.11-slim

RUN useradd -m myuser

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R myuser:myuser /app

USER myuser


EXPOSE 8000
EXPOSE 8501

#YAML Should ovveride --continue with YAML tommorow!
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
