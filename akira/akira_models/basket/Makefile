IMAGENAME=eugenepy/basket
TAG=latest

# docker relatived
builder:
	docker build --target builder \
		--cache-from=${IMAGENAME}:builder \
		--tag ${IMAGENAME}:builder .

# Build the runtime stage, using cached compile stage:
build_runtime: builder
	docker build \
		--cache-from=${IMAGENAME}:builder,${IMAGENAME}:${TAG} \
		--tag ${IMAGENAME}:${TAG} .

cleanup:
	docker rmi -f $(docker images | grep "none" | awk '/ / { print $3 }')
	docker rm $(docker ps -a -q)