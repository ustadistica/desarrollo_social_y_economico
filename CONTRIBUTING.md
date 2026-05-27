# Guia de Contribucion -- Ustadistica 2026-I

## Git Flow

```
main        <- Produccion. Solo codigo validado y final.
develop     <- Rama de integracion diaria del equipo.
feature/*   <- Ramas individuales por tarea/issue.
```

### Regla de Oro

> **Prohibido push directo a `main`.** Todo cambio requiere Pull Request aprobado.

## Flujo de Trabajo

1. **Crear rama** desde `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/nombre-descriptivo
   ```

2. **Trabajar** en tu rama con commits descriptivos.

3. **Crear Pull Request** hacia `develop`:
   - Titulo claro y conciso.
   - Descripcion de que se hizo y por que.
   - Asignar al menos un reviewer.

4. **Review y merge**: un companero revisa y aprueba.

## Convenciones de Commits

```
tipo: descripcion corta

Tipos validos:
  feat:     Nueva funcionalidad
  fix:      Correccion de bug
  data:     Cambios en datos o ingesta
  docs:     Documentacion
  refactor: Refactorizacion
  test:     Tests
  chore:    Mantenimiento
```

## Instalación Limpia y Configuración
Para asegurar un entorno de trabajo reproducible, siga estos pasos:

1. **Clonar el repositorio.**
2. **Crear un entorno virtual:** `python -m venv venv`
3. **Activar el entorno:** `.\venv\Scripts\activate` (Windows) o `source venv/bin/activate` (Mac/Linux).
4. **Instalar dependencias en modo editable:** `pip install -e .`
5. **Configurar variables de entorno:** Copiar `pipeline/.env.example` a `pipeline/.env` y ajustar las rutas.

---

## Convenciones de Desarrollo

### Importaciones (Import Conventions)
Para evitar dependencias circulares y rutas absolutas fallidas:
- Use siempre rutas relativas dentro del paquete `pipeline`.
- Ejemplo: `from ..utils import logger` en lugar de `import pipeline.utils.logger`.
- No use `sys.path.append` en scripts productivos.

### Estructura de Datos
- **Bronze:** Nunca modifique manualmente los archivos en `data/bronze/`.
- **Git Tracking:** No suba archivos `.parquet`, `.csv` o `.xlsx` pesados. Use el `.gitignore` proporcionado.

---

## Roles del Equipo

| Rol | Responsabilidad | KPI |
|-----|----------------|-----|
| Lider de Proyecto (PM) | Comunicacion con el Director, gestion Kanban, modera Stand-ups | 100% Issues asignados |
| Ingeniero de Datos | Ingesta, limpieza, validacion, pipeline reproducible | 0 nulos sin documentar |
| Analista Principal | Modelado estadistico, validacion de supuestos | Supuestos validados |
| Gestor del Conocimiento | Documentacion, README, docs/ | README actualizado por Sprint |

## Definition of Done (DoD)

Un entregable esta **DONE** cuando:

- [ ] El codigo pasa los tests básicos (`pytest`).
- [ ] El codigo fue revisado en PR por al menos un companero.
- [ ] La documentacion relevante fue actualizada en `documentacion_tecnica/`.
- [ ] Los datos generados son reproducibles mediante la CLI `socioeco-pipeline`.
- [ ] No hay secretos ni credenciales en el codigo.
