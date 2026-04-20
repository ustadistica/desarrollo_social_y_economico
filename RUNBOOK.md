# 📙 RUNBOOK - Gestión del Pipeline (Operaciones)

Guía rápida operativa para el equipo o auditores que deseen replicar o diagnosticar el proceso Medallion desde su ambiente local.

## 1. Configuración de Entorno (Setup)
1. **Requerimiento:** Verifica tener Python >=3.9 instalado. Descarga el repo de GIT.
2. **Dependencias:**
   ```powershell
   pip install -e .
   ```
3. **Validar las fuentes Externas:**
   Asegúrate de que la colección monstruosa de ~10GB cruda (CSVs de DANE en carpetas `CENSO 2018`, `EMICRON 2024`, etc.) repose correctamente en `../Datos/` o en tu ruta `.env` para que el recolector Bronze las audite. Aunque no estén completas, el orquestador generará su reporte sin caerse usando *bypass seguro*.

## 2. Ejecución Controlada

### 🔨 Capa Bronze (Raw)
* **Comando:** `python run_bronze.py` o `make bronze`
* **¿Qué hace?** Lee archivos brutos masivos, verifica chunks y los asimila bajo un esquema codificado en Parquet (`datos/bronze/`).
* **Verificación:** Revisa la auditoría en `documentacion_tecnica/BRONZE_VALIDATION_REPORT.md`

### 🥈 Capa Silver (Aggregated)
* **Comando:** `python run_silver.py` o `make silver`
* **¿Qué hace?** Filtra basuras, ejecuta DuckDB o Arrow sobre el mar de parquets. Agrega cada subconjunto (Conteo contratos, peso fex_c total, etc.) anclándolo obligatoriamente bajo el grano territorial (divipola) y temporal.
* **Verificación:** Revisa la limpieza en `documentacion_tecnica/SILVER_DATA_QUALITY_REPORT.md`. Todo debe estar limpio a grano `Municipio-Año`.

### 👑 Capa Gold (Facts & Dimensions)
* **Comando:** `python run_gold.py` o `make gold`
* **¿Qué hace?** Compila los esquemas Star Schema, verifica unicidad, constata joins y libera el OBT final integrador al `latest/` precalculando estadísticos analíticos exigidos.
* **Verificación:** Revisa los logs en `documentacion_tecnica/GOLD_VALIDATION_REPORT.md`.

### 🚀 Automatización Directa (Recomendada)
Para actualizar toda tu analítica a la vez sin fricción:
* **Comando:** `python run_all.py` o `make all`

## 3. Fallbacks, Casos de Error y Soluciones Comunes

| Error | Causa Raíz | Acción a tomar |
|-------|------------|----------------|
| `ModuleNotFoundError: No module named 'pipeline'` | No hiciste el `pip install -e .` o la estructura en path falló. | El script implementa un autoloader que inyecta el modulo `pipeline`. Comprueba que ejecutaste desde la carpeta raíz. |
| Reporte Silver dice `FAILED` pero el pipeline no crashea | El Bronze no detectó tus fuentes. Está haciendo early exit por seguridad técnica para no purgar datos. | Comprueba que descargaste los datos de `SECOP_II_Contratos.csv` correctamente mapeados en formato original. |
| DuckDB `Binder Error` | DANE cambió drásticamente sus headers de EMICRON. | Ningún problema fatal; `clean_emicron.py` ahora usa una lectura difusa vía PyArrow para resistir hasta un 100% de cambios asimétricos de columnas. |
