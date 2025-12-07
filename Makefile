.PHONEY: up
up:
	docker compose -f ./docker-compose.yaml up

.PHONEY: up-detached
up-detached:
	docker compose -f ./docker-compose.yaml up -d

.PHONEY: down
down:
	docker compose -f docker-compose.yaml down

.PHONEY: remove-containers
remove-containers:
	docker rm -f $$(docker ps -aq)

.PHONEY: remove-images
remove-images:
	docker rmi -f $$(docker images -aq)

.PHONEY: remove-volumes
remove-volumes:
	docker volume prune --all --force