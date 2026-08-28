# Construction de l'extension. Étape séparée : Node ne sert qu'à produire l'archive, et
# rien de cet étage ne subsiste dans l'image finale.
#
# Le paquet embarqué est **neutre** : aucune adresse de portail n'y est inscrite. C'est ce
# qui permet à tout le monde de déployer la même image publiée. Le portail y glisse sa
# propre adresse au moment du téléchargement (voir portail/__init__.py).
FROM node:22-slim AS extension

WORKDIR /build
COPY extension/package.json extension/package-lock.json ./
RUN npm ci
COPY extension/ ./
RUN npm run paquet


FROM python:3.12-slim

WORKDIR /app

# Données du dépôt nécessaires au moteur (prompts, taxonomie, schéma) et au portail
COPY prompts/ prompts/
COPY docs/ docs/
# Le portail publie corpus/RESULTATS.md sur /calibration : sans lui, la page tombe en
# 500. Les captures de pages réelles restent dehors, écartées par .dockerignore :
# elles ne sont pas versionnées non plus, pour la même raison de droit d'auteur.
COPY corpus/ corpus/
COPY schema/ schema/
COPY api/ api/

RUN pip install --no-cache-dir ./api

# Paquet d'extension embarqué. Un volume monté sur /paquets prend le dessus dès qu'il
# contient une version plus haute : mettre l'extension à jour ne demande donc pas de
# reconstruire l'image, et une image neuve n'arrive jamais les mains vides.
COPY --from=extension /build/lynceus-extension-v*.zip /app/paquets-image/

ENV LYNCEUS_RACINE_DONNEES=/app \
    LYNCEUS_PORTAIL_PAQUETS=/paquets,/app/paquets-image

EXPOSE 8000
CMD ["uvicorn", "lynceus.main:creer_application", "--factory", "--host", "0.0.0.0", "--port", "8000"]
