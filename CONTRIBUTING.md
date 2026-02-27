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

## Roles del Equipo

| Rol | Responsabilidad | KPI |
|-----|----------------|-----|
| Lider de Proyecto (PM) | Comunicacion con el Director, gestion Kanban, modera Stand-ups | 100% Issues asignados |
| Ingeniero de Datos | Ingesta, limpieza, validacion, pipeline reproducible | 0 nulos sin documentar |
| Analista Principal | Modelado estadistico, validacion de supuestos | Supuestos validados |
| Gestor del Conocimiento | Documentacion, README, docs/ | README actualizado por Sprint |

## Definition of Done (DoD)

Un entregable esta **DONE** cuando:

- [ ] El codigo pasa todos los tests (`poetry run pytest`)
- [ ] El codigo fue revisado en PR por al menos un companero
- [ ] La documentacion relevante fue actualizada
- [ ] Los datos generados son reproducibles desde el pipeline
- [ ] No hay secretos ni credenciales en el codigo
