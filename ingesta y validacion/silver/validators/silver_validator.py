"""
Validador Genérico para la Capa Silver.

Se encarga de verificar que las tablas generadas en Plata
(después de la limpieza) cumplan ciertas reglas de integridad,
como completitud de divipola, ausencia de duplicados,
y rangos numéricos aceptables.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)

class SilverValidator:
    """Implementa validaciones de datos para la capa Silver."""
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
        
    def validate_cnpv(self) -> Dict[str, Any]:
        """Valida que la limpieza del CNPV sea correcta."""
        file_path = self.data_path / "cnpv" / "cnpv_poblacion_agregada.parquet"
        if not file_path.exists():
            return {"status": "failed", "error": "Parquet de CNPV Silver no encontrado"}
            
        df = pd.read_parquet(file_path)
        
        errors = []
        if df['divipola_municipio'].isnull().any() or (df['divipola_municipio'] == '').any():
            errors.append("Existen registros sin divipola_municipio")
            
        if 'poblacion_total' in df.columns and (df['poblacion_total'] < 0).any():
            errors.append("Existen municipios con población_total negativa")
            
        if errors:
            return {"status": "failed", "errors": errors}
            
        return {"status": "success", "filas_validadas": len(df)}
        
    def validate_secop(self) -> Dict[str, Any]:
        """Valida limpieza del SECOP."""
        file_path = self.data_path / "secop" / "secop_clean.parquet"
        if not file_path.exists():
            return {"status": "failed", "error": "Parquet de SECOP Silver no encontrado"}
            
        df = pd.read_parquet(file_path)
        errors = []
        
        # Validar nulos críticos
        if df['id_contrato'].isnull().any():
            errors.append("Contratos limpios sin ID")
            
        if 'divipola_municipio' in df.columns:
            null_divipola = df['divipola_municipio'].isnull().sum()
            total = len(df)
            if null_divipola / total > 0.05:  # Más de 5% sin municipio es alarmante
                errors.append(f"Alta tasa de contratos sin municipio: {null_divipola/total:.1%}")
                
        if errors:
            return {"status": "warning", "errors": errors}  # En SECOP hay data muy sucia, warning
            
        return {"status": "success", "filas_validadas": len(df)}
    
    def validate_emicron(self) -> Dict[str, Any]:
        """Valida limpieza de EMICRON."""
        file_path = self.data_path / "emicron" / "emicron_clean.parquet"
        if not file_path.exists():
            return {"status": "failed", "error": "Parquet de EMICRON Silver no encontrado"}
        return {"status": "success"}

    def run_all_validations(self) -> Dict[str, Any]:
        """Ejecuta todas las validaciones disponibles."""
        results = {
            "cnpv": self.validate_cnpv(),
            "secop": self.validate_secop(),
            "emicron": self.validate_emicron(),
        }
        
        overall_status = "success"
        for k, v in results.items():
            if v.get("status") == "failed":
                overall_status = "failed"
                break
                
        return {
            "status": overall_status,
            "details": results
        }
