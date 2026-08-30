docker-up:
	@echo "Starting docker containers..."
	@docker compose -f docker/docker-compose.yml up -d -- build

docker-down:
	@echo "Stopping docker containers..."
	@docker compose -f docker/docker-compose.yml down