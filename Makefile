
staging_up:
	docker-compose up -d

staging_down:
	docker-compose down
	docker volume prune


