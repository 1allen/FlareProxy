.PHONY: help build test run clean

IMAGE_NAME=flareproxy
TEST_IMAGE_NAME=flareproxy-test

help:
	@echo "Available targets:"
	@echo "  make build    - Build the Docker image"
	@echo "  make test     - Run tests in Docker"
	@echo "  make run      - Run the proxy server locally"
	@echo "  make clean    - Remove Docker images"

build:
	docker build -t $(IMAGE_NAME) .

test:
	docker build -t $(TEST_IMAGE_NAME) .
	docker run --rm $(TEST_IMAGE_NAME) python -m unittest test_flareproxy.py

run:
	docker run --rm -p 8080:8080 --name $(IMAGE_NAME) $(IMAGE_NAME)

clean:
	docker rmi $(IMAGE_NAME) $(TEST_IMAGE_NAME) 2>/dev/null || true