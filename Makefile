SERVICES = data-pipeline position-manager

TOP = akira-env_
VOLUMES = kafka_data mongodb

build_all: ${SERVICES}

${SERVICES}:
	docker-compose -f docker-compose.yml build $@

staging_up:
	docker-compose -f docker-compose.yml up -d

staging_down:
	docker-compose down
	docker volume prune
	