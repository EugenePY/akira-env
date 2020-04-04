IMAGENAME=eugenepy/akira-data
TAG=latest

# docker relatived
builder:
	docker build --target builder \
		--cache-from=${IMAGENAME}:builder \
		--tag faust-rocksdb:latest .

# Build the runtime stage, using cached compile stage:
build_runtime: builder test
	docker build \
		--cache-from=${IMAGENAME}:builder,${IMAGENAME}:${TAG} \
		--tag ${IMAGENAME}:${TAG} .

test_image:
	docker run ${IMAGENAME}:${TAG} pytest

test_staging: build_runtime
	docker-compose -f docker-compose.yml up -d

down_staging: 
	docker-compose -f docker-compose.yml down

run: test_staging
	python script/run_websocket --kafka_host localhost:9092 --max_retry 5 1 2 3 4 5 6 7 8 

cleanup:
	docker rmi -f $(docker images | grep "none" | awk '/ / { print $3 }')
	docker rm $(docker ps -a -q)