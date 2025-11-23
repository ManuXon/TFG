# ========== VARIABLES ==========
DEV_COMPOSE = docker-compose.dev.yml
PROD_COMPOSE = docker-compose.prod.yml

# Default target
.DEFAULT_GOAL := help

# ========== COMMANDS ==========

help:
	@echo ""
	@echo "🚀 Available commands:"
	@echo "------------------------------------"
	@echo "make dev       → Run DEV environment (hot reload, mounts)"
	@echo "make prod      → Run PROD environment (optimized build)"
	@echo "make stop      → Stop all containers"
	@echo "make rebuild   → Rebuild all images (for the active compose)"
	@echo "make logs      → Show combined logs"
	@echo "make ps        → Show running containers"
	@echo "make clean     → Remove all containers & images"
	@echo "------------------------------------"
	@echo ""

# ========== DEV MODE ==========
dev:
	@echo "🧠 Starting DEV environment with hot reload..."
	docker compose -f $(DEV_COMPOSE) up --build

# ========== PROD MODE ==========
prod:
	@echo "🚀 Starting PROD environment..."
	docker compose -f $(PROD_COMPOSE) up --build -d

# ========== STOP ==========
stop:
	@echo "🛑 Stopping all containers..."
	docker compose -f $(DEV_COMPOSE) down || true
	docker compose -f $(PROD_COMPOSE) down || true

# ========== REBUILD ==========
rebuild:
	@echo "🔁 Rebuilding containers..."
	docker compose -f $(DEV_COMPOSE) build --no-cache
	docker compose -f $(PROD_COMPOSE) build --no-cache

# ========== LOGS ==========
logs:
	@echo "📜 Showing logs..."
	docker compose -f $(DEV_COMPOSE) logs -f || docker compose -f $(PROD_COMPOSE) logs -f

# ========== STATUS ==========
ps:
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ========== CLEAN ==========
clean:
	@echo "🧹 Removing containers and images..."
	docker compose -f $(DEV_COMPOSE) down --rmi all --volumes --remove-orphans || true
	docker compose -f $(PROD_COMPOSE) down --rmi all --volumes --remove-orphans || true
