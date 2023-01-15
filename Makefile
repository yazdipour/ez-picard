GIT_HEAD_REF := $(shell git rev-parse HEAD)
EVAL_IMAGE_NAME := text-to-sql-ez-picard
DOCKERHUB_USER := shayazdipour

BASE_DIR := $(shell pwd)

BUILDKIT_BUILDER ?= buildx-local
BASE_IMAGE := pytorch/pytorch:1.9.0-cuda11.1-cudnn8-devel
EVAL_IMAGE_NAME := tscholak/text-to-sql-eval
GIT_HEAD_REF := 6a252386bed6d4233f0f13f4562d8ae8608e7445

.PHONY: ez-build
ez-build:
	docker build -t $(EVAL_IMAGE_NAME):$(GIT_HEAD_REF) -f Dockerfile .

.PHONY: pull-eval-image
pull-eval-image:
	docker pull $(EVAL_IMAGE_NAME):$(GIT_HEAD_REF)

.PHONY: ez
ez: pull-eval-image
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
		--mount type=bind,source=$(BASE_DIR)/seq2seq/serve_seq2seq.py,target=/app/seq2seq/serve_seq2seq.py \
		$(EVAL_IMAGE_NAME):$(GIT_HEAD_REF) \
		/bin/bash -c "pip install python-multipart==0.0.5; python seq2seq/serve_seq2seq.py configs/serve.json"

.PHONY: api
api:
	docker-compose build api
	docker-compose up

.PHONY: ui
ui:
	docker-compose build ui
	docker-compose up