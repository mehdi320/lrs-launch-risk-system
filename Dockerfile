# LRS™ — image unique pour les deux surfaces web (pilote FastAPI +
# app Streamlit), qui partagent le même code et les mêmes dépendances.
# Le service à lancer est choisi par la commande (voir docker-compose.yml
# ou --entrypoint/CMD au run) ; ce Dockerfile installe et copie le code.
#
# Squelette non testé en conditions réelles (pas de démon Docker
# disponible pendant son écriture) — build/run à valider avant tout
# déploiement, voir DEPLOYMENT.md.

FROM python:3.11-slim

WORKDIR /app

# build-essential : au cas où une dépendance (ex. lxml, utilisé par
# trafilatura) n'aurait pas de wheel précompilée pour la plateforme cible.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home lrs \
    && chown -R lrs:lrs /app
USER lrs

EXPOSE 8501 8600

# Commande par défaut : le pilote FastAPI. docker-compose.yml définit un
# second service (même image) qui la surcharge pour lancer Streamlit.
CMD ["uvicorn", "pilot_server:app", "--host", "0.0.0.0", "--port", "8600"]
