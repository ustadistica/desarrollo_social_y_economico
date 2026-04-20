"""
Generación de reportes de calidad de datos.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)


def generate_quality_report(
    validation_results: Dict[str, Any],
    output_path: Optional[Path] = None,
    template: str = 'default',
) -> Dict[str, Any]:
    """
    Generar reporte HTML de calidad de datos.
    
    Parameters:
    - validation_results: Resultados de validaciones
    - output_path: Ruta de salida para el reporte
    - template: Nombre de plantilla ('default', 'executive', 'detailed')
    
    Returns:
    - Dict con metadata del reporte generado
    """
    if output_path is None:
        from config.settings import settings
        output_path = settings.get_quality_report_path()
    
    output_path = Path(output_path)
    
    if not output_path.suffix:
        output_path = output_path / f"quality_report_{datetime.now().strftime('%Y-%m-%d')}.html"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generar HTML
    html_content = _generate_html_report(validation_results, template)
    
    # Guardar
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Reporte de calidad generado: {output_path}")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'timestamp': datetime.now().isoformat(),
        'total_validations': validation_results.get('total_validations', 0),
        'total_errors': validation_results.get('total_errors', 0),
        'total_warnings': validation_results.get('total_warnings', 0),
    }


def _generate_html_report(results: Dict[str, Any], template: str) -> str:
    """
    Generar contenido HTML del reporte.
    
    Parameters:
    - results: Resultados de validaciones
    - template: Tipo de plantilla
    
    Returns:
    - String con HTML
    """
    # Determinar estado general
    status = results.get('status', 'unknown')
    status_color = {
        'success': '#28a745',
        'warning': '#ffc107',
        'error': '#dc3545',
        'unknown': '#6c757d',
    }.get(status, '#6c757d')
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Calidad de Datos - Pipeline ETL/ELT</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .status-badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; font-weight: bold; background: {status_color}; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .summary-card .number {{ font-size: 2.5em; font-weight: bold; color: #667eea; }}
        .summary-card .label {{ color: #666; margin-top: 5px; }}
        .section {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .section h2 {{ color: #667eea; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #333; }}
        tr:hover {{ background: #f8f9fa; }}
        .error {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .success {{ color: #28a745; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }}
        .badge-error {{ background: #f8d7da; color: #721c24; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 0.9em; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Reporte de Calidad de Datos</h1>
            <p>Pipeline ETL/ELT - Observatorio de Desarrollo Socioeconómico</p>
            <p style="margin-top: 15px;">
                <span class="status-badge">{status.upper()}</span>
                <span style="margin-left: 15px;">📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
            </p>
        </div>
        
        {_generate_summary_section(results)}
        {_generate_layer_sections(results)}
        {_generate_errors_section(results)}
        
        <div class="footer">
            <p>Generado automáticamente por el Pipeline de Calidad de Datos</p>
            <p>Consultorio de Estadística USTA - 2026</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def _generate_summary_section(results: Dict[str, Any]) -> str:
    """Generar sección de resumen."""
    total = results.get('total_validations', 0)
    errors = results.get('total_errors', 0)
    warnings = results.get('total_warnings', 0)
    success = total - errors - warnings
    
    # Calcular porcentaje de éxito
    success_rate = (success / total * 100) if total > 0 else 0
    
    return f"""
        <div class="summary">
            <div class="summary-card">
                <div class="number">{total}</div>
                <div class="label">Validaciones Totales</div>
            </div>
            <div class="summary-card">
                <div class="number" style="color: #28a745;">{success}</div>
                <div class="label">Exitosas</div>
            </div>
            <div class="summary-card">
                <div class="number" style="color: #ffc107;">{warnings}</div>
                <div class="label">Advertencias</div>
            </div>
            <div class="summary-card">
                <div class="number" style="color: #dc3545;">{errors}</div>
                <div class="label">Errores</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Tasa de Éxito</h2>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {success_rate}%;"></div>
            </div>
            <p style="text-align: center; margin-top: 10px;">
                <strong>{success_rate:.1f}%</strong> de validaciones exitosas
            </p>
        </div>
    """


def _generate_layer_sections(results: Dict[str, Any]) -> str:
    """Generar secciones por capa."""
    html = ""
    
    # Capa Bronce
    if 'resultados_por_fuente' in results:
        html += """
        <div class="section">
            <h2>🥉 Capa Bronce (Datos Crudos)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Fuente</th>
                        <th>Archivos Validados</th>
                        <th>Errores</th>
                        <th>Advertencias</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for fuente, detalle in results['resultados_por_fuente'].items():
            estado = 'success' if detalle.get('errores', 0) == 0 else 'error'
            html += f"""
                    <tr>
                        <td><strong>{fuente}</strong></td>
                        <td>{detalle.get('archivos_validados', 0)}</td>
                        <td class="{'error' if detalle.get('errores', 0) > 0 else ''}">{detalle.get('errores', 0)}</td>
                        <td class="{'warning' if detalle.get('warnings', 0) > 0 else ''}">{detalle.get('warnings', 0)}</td>
                        <td><span class="badge badge-{estado}">{estado.upper()}</span></td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    # Capa Plata
    if 'tablas_validadas' in results and 'integridad_referencial' in results:
        html += """
        <div class="section">
            <h2>🥈 Capa Plata (Datos Transformados)</h2>
            <p><strong>Tablas validadas:</strong> """ + str(results.get('tablas_validadas', 0)) + """</p>
            <p><strong>Integridad Referencial:</strong> """
        
        if results.get('integridad_referencial_valida'):
            html += '<span class="badge badge-success">VÁLIDA</span>'
        else:
            html += '<span class="badge badge-error">CON PROBLEMAS</span>'
        
        html += """
        </div>
        """
    
    # Capa Oro
    if 'datamarts_validados' in results:
        html += """
        <div class="section">
            <h2>🥇 Capa Oro (Data Marts)</h2>
            <p><strong>Data Marts validados:</strong> """ + str(results.get('datamarts_validados', 0)) + """</p>
            <p><strong>Tablas validadas:</strong> """ + str(results.get('tablas_validadas', 0)) + """</p>
        </div>
        """
    
    return html


def _generate_errors_section(results: Dict[str, Any]) -> str:
    """Generar sección de errores y advertencias."""
    detalles = results.get('detalles', [])
    
    if not detalles:
        return ""
    
    html = """
    <div class="section">
        <h2>⚠️ Detalles de Validación</h2>
        <table>
            <thead>
                <tr>
                    <th>Elemento</th>
                    <th>Nivel</th>
                    <th>Mensaje</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for detalle in detalles[:50]:  # Limitar a 50 registros
        nivel = detalle.get('nivel', 'info')
        badge_class = {
            'error': 'badge-error',
            'warning': 'badge-warning',
            'info': 'badge-success',
        }.get(nivel, 'badge-success')
        
        html += f"""
            <tr>
                <td>{detalle.get('tabla', detalle.get('archivo', 'N/A'))}</td>
                <td><span class="badge {badge_class}">{nivel.upper()}</span></td>
                <td>{detalle.get('mensaje', 'Sin descripción')}</td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html


def generate_json_report(
    validation_results: Dict[str, Any],
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Generar reporte JSON de calidad de datos.
    
    Parameters:
    - validation_results: Resultados de validaciones
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata del reporte
    """
    import json
    
    if output_path is None:
        from config.settings import settings
        output_path = settings.QUALITY_REPORTS_PATH / f"quality_metrics_{datetime.now().strftime('%Y-%m-%d')}.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Agregar metadata
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'pipeline_version': '1.0.0',
            'project': 'Observatorio de Desarrollo Socioeconómico',
        },
        'results': validation_results,
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Reporte JSON generado: {output_path}")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de resultados
    resultados_ejemplo = {
        'status': 'warning',
        'total_validations': 25,
        'total_errors': 2,
        'total_warnings': 3,
        'resultados_por_fuente': {
            'dane_cnpv': {'archivos_validados': 1, 'errores': 0, 'warnings': 0},
            'secop_ii': {'archivos_validados': 1, 'errores': 1, 'warnings': 1},
        },
        'tablas_validadas': 7,
        'integridad_referencial_valida': True,
        'datamarts_validados': 2,
        'detalles': [
            {'tabla': 'fact_contratacion', 'nivel': 'warning', 'mensaje': '5 montos negativos detectados'},
            {'tabla': 'secop_ii', 'nivel': 'error', 'mensaje': 'Checksum inválido'},
        ],
    }
    
    resultado = generate_quality_report(resultados_ejemplo)
    print(f"Reporte generado: {resultado}")
