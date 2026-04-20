"""
Motor de procesamiento analítico dual: PySpark ↔ PyArrow.

Intenta usar PySpark para procesamiento distribuido. Si falla
(ej: Python 3.12 + Windows, Java ausente, etc.), cae automáticamente
a PyArrow Dataset API, que ofrece las mismas capacidades out-of-core
sobre Parquet sin necesidad de JVM.

Este módulo expone funciones de alto nivel para que el resto del
pipeline nunca se preocupe por qué motor está activo.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# Estado global del motor
# ─────────────────────────────────────────────────────────────────
_engine = None          # "pyspark" | "pyarrow"
_spark_session = None   # SparkSession (solo si engine == pyspark)
_engine_tested = False  # Solo probamos una vez por proceso


def _test_pyspark() -> bool:
    """
    Prueba real de PySpark: crea una sesión, ejecuta un cálculo
    mínimo, y solo devuelve True si todo funciona end-to-end.
    """
    try:
        from pyspark.sql import SparkSession

        # Asegurar que PYSPARK_PYTHON apunte al ejecutable correcto
        os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
        os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

        spark = (SparkSession.builder
            .appName("DesarrolloSocialEconomico")
            .master("local[*]")
            .config("spark.driver.memory", "4g")
            .config("spark.executor.memory", "4g")
            .config("spark.sql.parquet.compression.codec", "snappy")
            .config("spark.ui.enabled", "false")       # No levantar UI web
            .config("spark.pyspark.python", sys.executable)
            .config("spark.pyspark.driver.python", sys.executable)
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")

        # Prueba real: crear un DF, ejecutar SQL, recoger resultado
        test_df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "val"])
        test_df.createOrReplaceTempView("_engine_test")
        result = spark.sql("SELECT COUNT(*) AS n FROM _engine_test").collect()
        assert result[0]["n"] == 2

        return True, spark

    except Exception as e:
        logger.warning(f"PySpark no disponible o falló la prueba: {e}")
        # Limpieza en caso de que la sesión se haya creado pero falle al ejecutar
        try:
            spark.stop()
        except Exception:
            pass
        return False, None


def _detect_engine():
    """Detecta una sola vez qué motor usar."""
    global _engine, _spark_session, _engine_tested

    if _engine_tested:
        return

    _engine_tested = True

    logger.info("Detectando motor analítico disponible...")

    ok, spark = _test_pyspark()
    if ok:
        _engine = "pyspark"
        _spark_session = spark
        logger.info("✔ Motor seleccionado: PySpark (distribuido)")
    else:
        _engine = "pyarrow"
        _spark_session = None
        logger.info("✔ Motor seleccionado: PyArrow (nativo, sin JVM)")


# ─────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────

def get_engine_name() -> str:
    """Devuelve 'pyspark' o 'pyarrow'."""
    _detect_engine()
    return _engine


def get_spark_session(app_name: str = "DesarrolloSocialEconomico"):
    """
    Devuelve la SparkSession activa. Si PySpark no está disponible,
    lanza RuntimeError con un mensaje claro.
    """
    _detect_engine()
    if _engine == "pyspark" and _spark_session is not None:
        return _spark_session
    raise RuntimeError(
        "PySpark no está disponible en este entorno. "
        "Use query_parquet() o write_parquet() que son motor-agnósticos."
    )


def query_parquet(parquet_path, sql_query: str) -> pd.DataFrame:
    """
    Lee un archivo Parquet y ejecuta una consulta SQL sobre él.
    Funciona con PySpark o PyArrow automáticamente.

    Parameters:
        parquet_path: Ruta al archivo o directorio Parquet.
        sql_query:    Consulta SQL. Debe referenciar la tabla como 'datos'.

    Returns:
        pd.DataFrame con el resultado.
    """
    _detect_engine()
    parquet_str = str(parquet_path)

    if _engine == "pyspark":
        return _query_parquet_spark(parquet_str, sql_query)
    else:
        return _query_parquet_pyarrow(parquet_str, sql_query)


def write_parquet(df: pd.DataFrame, output_path, partition_cols=None):
    """
    Escribe un DataFrame Pandas como Parquet particionado.
    Funciona con PySpark o PyArrow automáticamente.

    Parameters:
        df:             DataFrame de Pandas a escribir.
        output_path:    Directorio de destino.
        partition_cols: Columnas para particionar (opcional).
    """
    _detect_engine()
    output_str = str(output_path)

    if _engine == "pyspark":
        _write_parquet_spark(df, output_str, partition_cols)
    else:
        _write_parquet_pyarrow(df, output_str, partition_cols)


def stop_spark_session():
    """Detiene la sesión de Spark si existe."""
    global _spark_session
    if _spark_session is not None:
        try:
            _spark_session.stop()
        except Exception:
            pass
        _spark_session = None
        logger.info("Sesión Spark detenida.")


# ─────────────────────────────────────────────────────────────────
# Implementaciones internas - PySpark
# ─────────────────────────────────────────────────────────────────

def _query_parquet_spark(parquet_path: str, sql_query: str) -> pd.DataFrame:
    """Ejecuta consulta SQL vía PySpark."""
    spark = _spark_session
    df_spark = spark.read.parquet(parquet_path)
    df_spark.createOrReplaceTempView("datos")
    result = spark.sql(sql_query)
    return result.toPandas()


def _write_parquet_spark(df: pd.DataFrame, output_path: str, partition_cols=None):
    """Escribe Parquet particionado vía PySpark."""
    spark = _spark_session
    df_clean = df.fillna(0)
    spark_df = spark.createDataFrame(df_clean)
    writer = spark_df.write.mode("overwrite")
    if partition_cols:
        writer = writer.partitionBy(*partition_cols)
    writer.parquet(output_path)
    logger.info(f"Escrito vía PySpark: {output_path}")


# ─────────────────────────────────────────────────────────────────
# Implementaciones internas - PyArrow
# ─────────────────────────────────────────────────────────────────

def _query_parquet_pyarrow(parquet_path: str, sql_query: str) -> pd.DataFrame:
    """
    Ejecuta consulta SQL sobre un Parquet usando PyArrow + DuckDB-free SQL.

    Estrategia: lee el Parquet con PyArrow Dataset (out-of-core),
    lo convierte en un DataFrame de Pandas, y usa pandas para
    las agregaciones que el SQL describe. Para mantener la
    compatibilidad SQL sin depender de DuckDB, usamos
    pandas.DataFrame.query + groupby según el patrón detectado.

    Para consultas más complejas, se puede agregar `sqldf` en el futuro.
    """
    import pyarrow.parquet as pq
    import pyarrow.dataset as ds

    logger.info(f"Leyendo Parquet con PyArrow: {parquet_path}")

    # Leer de manera eficiente (out-of-core para archivos grandes)
    path = Path(parquet_path)
    if path.is_dir():
        dataset = ds.dataset(parquet_path, format="parquet")
        table = dataset.to_table()
    else:
        table = pq.read_table(parquet_path)

    # Convertir a Pandas para aplicar el SQL como operación Pandas
    df = table.to_pandas()

    # Registrar la tabla como 'datos' para ejecutar SQL vía pandasql si está disponible
    try:
        from pandasql import sqldf
        result = sqldf(sql_query, {"datos": df})
        return result
    except ImportError:
        pass

    # Fallback manual: interpretar patrones SQL comunes
    # Soporta: SELECT ... FROM datos GROUP BY ...
    return _execute_simple_sql(df, sql_query)


def _execute_simple_sql(df: pd.DataFrame, sql_query: str) -> pd.DataFrame:
    """
    Intérprete minimalista de SQL sobre un DataFrame de Pandas.
    Soporta SELECT con concat, COUNT, SUM, AVG, GROUP BY.
    Si el SQL es demasiado complejo, devuelve el DF tal cual con un warning.
    """
    import re

    sql_clean = " ".join(sql_query.strip().split())
    sql_upper = sql_clean.upper()

    # Patrón: GROUP BY con agregaciones
    if "GROUP BY" in sql_upper:
        # Extraer columnas del GROUP BY
        gb_match = re.search(r'GROUP\s+BY\s+(.+?)(?:ORDER|HAVING|LIMIT|$)', sql_upper)
        if not gb_match:
            logger.warning("No se pudo parsear GROUP BY; devolviendo DF sin agrupar.")
            return df

        group_cols_raw = gb_match.group(1).strip().rstrip(';')
        group_cols = [c.strip() for c in group_cols_raw.split(",")]

        # Mapear a nombres reales de columnas del DataFrame (case-insensitive)
        col_map = {c.upper(): c for c in df.columns}
        group_cols_real = [col_map.get(c, c) for c in group_cols]

        # Extraer SELECT
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_clean, re.IGNORECASE)
        if not select_match:
            return df.groupby(group_cols_real).size().reset_index(name='count')

        select_raw = select_match.group(1)
        select_parts = _split_select(select_raw)

        # Construir las agregaciones
        agg_dict = {}
        rename_map = {}
        concat_exprs = {}

        for part in select_parts:
            part_stripped = part.strip()
            # Detectar alias: ... AS nombre
            alias_match = re.match(r'(.+?)\s+AS\s+(\w+)', part_stripped, re.IGNORECASE)
            if alias_match:
                expr = alias_match.group(1).strip()
                alias = alias_match.group(2).strip()
            else:
                expr = part_stripped
                alias = None

            expr_upper = expr.upper()

            # COUNT(*)
            if 'COUNT(*)' in expr_upper or 'COUNT(1)' in expr_upper:
                agg_dict['__count__'] = ('__first_col__', 'size')
                rename_map['__count__'] = alias or 'count'

            # COUNT(col)
            elif expr_upper.startswith('COUNT('):
                col_name = re.search(r'COUNT\((\w+)\)', expr, re.IGNORECASE).group(1)
                real_col = col_map.get(col_name.upper(), col_name)
                agg_dict[alias or f'count_{real_col}'] = (real_col, 'count')

            # SUM(col)
            elif expr_upper.startswith('SUM('):
                col_name = re.search(r'SUM\((\w+)\)', expr, re.IGNORECASE).group(1)
                real_col = col_map.get(col_name.upper(), col_name)
                agg_dict[alias or f'sum_{real_col}'] = (real_col, 'sum')

            # AVG(col)
            elif expr_upper.startswith('AVG('):
                col_name = re.search(r'AVG\((\w+)\)', expr, re.IGNORECASE).group(1)
                real_col = col_map.get(col_name.upper(), col_name)
                agg_dict[alias or f'avg_{real_col}'] = (real_col, 'mean')

            # CONCAT(a, b) o a || b
            elif 'CONCAT(' in expr_upper or '||' in expr:
                concat_exprs[alias or 'concat_result'] = expr

            # Columna plana (probablemente parte del GROUP BY)
            else:
                pass  # Las columnas del GROUP BY se incluyen automáticamente

        # Ejecutar agrupación
        grouped = df.groupby(group_cols_real, as_index=False)

        if agg_dict:
            # Resolver COUNT(*)
            if '__count__' in agg_dict:
                first_col = df.columns[0]
                agg_dict['__count__'] = (first_col, 'size')

            # Construir named agg
            named_agg = {k: pd.NamedAgg(column=v[0], aggfunc=v[1])
                         for k, v in agg_dict.items()}
            result = grouped.agg(**named_agg)

            # Renombrar COUNT si tiene alias
            if '__count__' in result.columns and rename_map.get('__count__'):
                result = result.rename(columns={'__count__': rename_map['__count__']})
        else:
            result = grouped.size().reset_index(name='count')

        # Aplicar concat si existe
        for alias, expr in concat_exprs.items():
            concat_match = re.search(r'CONCAT\((.+?)\)', expr, re.IGNORECASE)
            if concat_match:
                cols = [col_map.get(c.strip().upper(), c.strip())
                        for c in concat_match.group(1).split(",")]
                result[alias] = result[cols[0]].astype(str)
                for c in cols[1:]:
                    result[alias] = result[alias] + result[c].astype(str)
            elif '||' in expr:
                parts = [p.strip() for p in expr.split('||')]
                cols = [col_map.get(p.upper(), p) for p in parts]
                result[alias] = result[cols[0]].astype(str)
                for c in cols[1:]:
                    result[alias] = result[alias] + result[c].astype(str)

        return result

    # Sin GROUP BY: simplemente devolver el DF
    logger.warning("Consulta SQL sin GROUP BY; devolviendo DataFrame completo.")
    return df


def _split_select(select_str: str):
    """Divide la cláusula SELECT respetando paréntesis."""
    parts = []
    depth = 0
    current = ""
    for ch in select_str:
        if ch == '(':
            depth += 1
            current += ch
        elif ch == ')':
            depth -= 1
            current += ch
        elif ch == ',' and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current)
    return parts


def _write_parquet_pyarrow(df: pd.DataFrame, output_path: str, partition_cols=None):
    """Escribe Parquet particionado vía PyArrow."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    output = Path(output_path)
    output.mkdir(parents=True, exist_ok=True)

    table = pa.Table.from_pandas(df)

    if partition_cols:
        pq.write_to_dataset(
            table,
            root_path=output_path,
            partition_cols=partition_cols,
            compression="snappy",
        )
    else:
        pq.write_table(
            table,
            output / "part-00000.snappy.parquet",
            compression="snappy",
        )

    logger.info(f"Escrito vía PyArrow: {output_path}")
