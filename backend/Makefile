DOCKER_VENV = .venv@docker

.PHONEY: reformat
reformat:
	docker compose -f ../docker-compose.yaml run --rm --no-deps backend ./scripts/reformat.sh

.PHONEY: test-unit
test-unit: ../docker-compose.yaml $(DOCKER_VENV)  # make sure docker-compose and DOCKER_VENV exist
	docker compose -f ../docker-compose.yaml run --rm --no-deps backend /app/$(DOCKER_VENV)/bin/pytest tests/unit