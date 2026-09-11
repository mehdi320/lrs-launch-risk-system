FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# La commande réelle (streamlit run app.py / uvicorn webhook_server:app)
# est fixée par service dans docker-compose.yml — même image pour les deux.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
