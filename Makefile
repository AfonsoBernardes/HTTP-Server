up:
	docker compose -f ./docker-compose.yaml up

up-detached:
	docker compose -f ./docker-compose.yaml up -d

down:
	docker compose -f docker-compose.yaml down

remove-containers:
	docker rm -f $$(docker ps -aq)

remove-images:
	docker rmi -f $$(docker images -aq)

remove-volumes:
	docker volume prune --all --force