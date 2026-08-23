FROM python:3.12-slim

WORKDIR /app

# Données du dépôt nécessaires au moteur (prompts, taxonomie, schéma)
COPY prompts/ prompts/
COPY docs/ docs/
COPY schema/ schema/
COPY api/ api/

RUN pip install --no-cache-dir ./api

ENV LYNCEUS_RACINE_DONNEES=/app
EXPOSE 8000
CMD ["uvicorn", "lynceus.main:creer_application", "--factory", "--host", "0.0.0.0", "--port", "8000"]
