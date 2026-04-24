# ==============================================================================
# Dockerfile — socioeco_pipeline
# Imagen para ejecutar el pipeline ETL/ELT Medallion
# ==============================================================================
# NOTA: Esta imagen NO incluye datos fuente (son demasiado pesados).
#       Los datos deben montarse como volumen al ejecutar el contenedor.
#
# Uso:
#   docker build -t socioeco-pipeline .
#   docker run -v /ruta/a/tus/Datos:/data -v ./pipeline/.env:/app/pipeline/.env socioeco-pipeline socioeco-pipeline
# ==============================================================================

FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar el proyecto (solo dependencias core, sin spark/geo)
COPY pyproject.toml ./
COPY pipeline/ ./pipeline/

RUN pip install --no-cache-dir -e .

# Copiar scripts de ejecución legacy (compatibilidad)
COPY run_bronze.py run_silver.py run_gold.py run_all.py ./

# Copiar ficheros auxiliares de documentación y configuración
COPY documentacion_tecnica/ ./documentacion_tecnica/
COPY app/ ./app/

# Crear directorios de datos de salida
RUN mkdir -p datos/bronze datos/plata datos/oro

# El entrypoint por defecto muestra ayuda del CLI
ENTRYPOINT ["python", "-m", "pipeline.cli"]
CMD ["--help"]
