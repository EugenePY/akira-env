SERVICES = data-pipeline baskets position-manager
SERVICE_PATH = data_pipeline akira_models/baskets position_manager


compile:
	docker build --target builder \
		--cache-from=eugenepy/$@:builder \
		--tag eugenepy/$@:builder .

.PHONY: compile 


build_runtime: compile
	$(foreach var,$(SERVICES),./a.out $(var);)
	docker build --target runtime \
		--cache-from=${IMAGENAME}:latest \
		--tag ${IMAGENAME}:latest .

.PHONY: build_runtime

staging_up: all
	docker-compose up -d

staging_down:
	docker-compose down
	docker volume prune