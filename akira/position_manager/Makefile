IMAGENAME=eugenepy/position-manager
TAG=latest

# docker relatived
builder:
	docker build --target builder \
		--cache-from=${IMAGENAME}:builder \
		--tag ${IMAGENAME}:builder .

# Build the runtime stage, using cached compile stage:
build_runtime: builder test
	docker build \
		--cache-from=${IMAGENAME}:builder,${IMAGENAME}:${TAG} \
		--tag ${IMAGENAME}:${TAG} .