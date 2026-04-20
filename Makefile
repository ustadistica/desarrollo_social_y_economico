.PHONY: install bronze silver gold all clean test

install:
	pip install -e .

bronze:
	python run_bronze.py

silver:
	python run_silver.py

gold:
	python run_gold.py

all:
	python run_all.py

clean:
	rm -rf datos/bronze/* datos/plata/* datos/gold/*
	rm -rf documentacion_tecnica/*_REPORT.md

test:
	pytest tests/
