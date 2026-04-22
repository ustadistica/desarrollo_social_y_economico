.PHONY: install bronze silver gold all clean test help

help:
	@echo "socioeco_pipeline - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  install  - Instalar el paquete en modo editable"
	@echo "  bronze   - Ejecutar capa Bronze (ingesta)"
	@echo "  silver   - Ejecutar capa Silver (limpieza)"
	@echo "  gold     - Ejecutar capa Gold (modelo estrella)"
	@echo "  all      - Ejecutar pipeline completo"
	@echo "  clean    - Limpiar datos generados"
	@echo "  test     - Ejecutar tests"

install:
	pip install -e .

bronze:
	python -m pipeline bronze

silver:
	python -m pipeline silver

gold:
	python -m pipeline gold

all:
	python -m pipeline all

clean:
	rm -rf datos/bronze/* datos/plata/* datos/oro/*
	rm -rf documentacion_tecnica/*_REPORT.md

test:
	pytest tests/
