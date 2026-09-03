.DEFAULT_GOAL := help

COMPOSE = docker compose

PRICING_FILE ?= "/Users/martin/Documents/perso/panneaux/SITE MARCHAND SIGNALISATION/Tableau Produits-Prix-Achat-Vente+Images dos.xlsx"

.PHONY: help up down restart logs shell migrate makemigrations build import-products apply-pricing seed

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
	@echo "  import-products  Importer les panneaux depuis Produits.txt (--clear)"
	@echo "  apply-pricing    Appliquer les prix depuis l'Excel (PRICING_FILE=...)"
	@echo "  seed          Import produits + prix en une commande"

up:
	$(COMPOSE) up --build -d
	$(COMPOSE) exec web uv run python manage.py migrate --no-input
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

import-products:
	$(COMPOSE) exec web uv run python manage.py import_products --clear

apply-pricing:
	$(COMPOSE) exec web uv run python manage.py apply_pricing --file $(PRICING_FILE)

seed: import-products apply-pricing
