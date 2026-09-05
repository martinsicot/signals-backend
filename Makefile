.DEFAULT_GOAL := help

COMPOSE = docker compose

.PHONY: help up down restart logs shell migrate makemigrations build import-catalog seed thumbnails

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "  up            Build + démarrer db, redis, api (migrations incluses)"
	@echo "  down          Arrêter et supprimer les containers"
	@echo "  restart       Redémarrer l'api uniquement"
	@echo "  logs          Suivre les logs de l'api"
	@echo "  shell         Shell Django interactif"
	@echo "  migrate       Appliquer les migrations"
	@echo "  makemigrations Créer les migrations"
	@echo "  build         Rebuild l'image Docker"
	@echo "  import-catalog Importer le catalogue depuis la grille de prix (--clear)"
	@echo "  seed          Alias de import-catalog"
	@echo "  thumbnails    Générer les vignettes WebP des images produits"

up:
	$(COMPOSE) up --build -d
	$(COMPOSE) exec web uv run python manage.py migrate --no-input
	$(COMPOSE) exec web uv run python manage.py generate_thumbnails
	@echo ""
	@echo "API disponible sur http://localhost:8000"
	@echo "Docs Swagger  : http://localhost:8000/api/docs/"

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart web

logs:
	$(COMPOSE) logs -f web

shell:
	$(COMPOSE) exec web uv run python manage.py shell

migrate:
	$(COMPOSE) exec web uv run python manage.py migrate --no-input

makemigrations:
	$(COMPOSE) exec web uv run python manage.py makemigrations

import-catalog:
	$(COMPOSE) exec web uv run python manage.py import_price_grid --clear

seed: import-catalog

thumbnails:
	$(COMPOSE) exec web uv run python manage.py generate_thumbnails
