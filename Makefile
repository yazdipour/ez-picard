GIT_HEAD_REF := $(shell git rev-parse HEAD)

EVAL_IMAGE_NAME := text-to-sql-ez-picard
DOCKERHUB_USER := shayazdipour
BASE_DIR := $(shell pwd)

.PHONY: ez-build
ez-build:
	docker build -t $(EVAL_IMAGE_NAME):$(GIT_HEAD_REF) -f Dockerfile .

# .PHONY: pull-eval-image
# pull-eval-image:
# 	docker pull $(EVAL_IMAGE_NAME):$(GIT_HEAD_REF)

.PHONY: ez-run
ez-run: ez-build
	mkdir -p -m 777 database
	mkdir -p -m 777 transformers_cache
	docker run \
		-it \
		--rm \
		--user 13011:13011 \
		-p 8000:8000 \
		--mount type=bind,source=$(BASE_DIR)/database,target=/database \
		--mount type=bind,source=$(BASE_DIR)/transformers_cache,target=/transformers_cache \
		--mount type=bind,source=$(BASE_DIR)/configs,target=/app/configs \
		$(EVAL_IMAGE_NAME):$(GIT_HEAD_REF) \
		/bin/bash -c "python seq2seq/serve_seq2seq.py configs/serve.json"

.PHONY: dc
dc:
	docker-compose build ez-picard
	docker-compose up

.PHONY: dz
dz:
	docker-compose build ez-picard
	docker-compose up ez-picard