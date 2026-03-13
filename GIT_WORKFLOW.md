# Guía de Git y Flujo de Trabajo

## 📋 Reglas del Repositorio

### ✅ Reglas Obligatorias

| Regla | Descripción |
|-------|-------------|
| ❌ **NUNCA** push directo a `main` | La rama main está protegida |
| ✅ **SIEMPRE** crear Pull Request | Todo cambio debe pasar por PR |
| 👥 **MÍNIMO 1 reviewer** por PR | Requiere aprobación antes de merge |
| 📝 **Commits descriptivos** | Usar convención establecida |

---

## 🔄 Flujo de Trabajo Recomendado

### 1. Crear Rama Nueva

```bash
git checkout main
git pull origin main
git checkout -b feature/nueva-funcionalidad
```

### 2. Hacer Cambios y Commit

```bash
git add .
git commit -m "tipo: descripción del cambio"
```

### 3. Push y Pull Request

```bash
git push origin feature/nueva-funcionalidad
# Crear PR en GitHub
```

---

## 📝 Convención de Commits

| Tipo | Cuándo Usar | Ejemplo |
|------|-------------|---------|
| `feat:` | Nueva funcionalidad | `feat: agregar migración DuckDB` |
| `fix:` | Corrección de bug | `fix: corregir NULLs en FKs` |
| `data:` | Cambios en datos | `data: cargar registros SECOP` |
| `docs:` | Documentación | `docs: agregar README migración` |
| `refactor:` | Refactorización | `refactor: optimizar ETL` |
| `chore:` | Mantenimiento | `chore: actualizar dependencias` |

### Ejemplos

```bash
# ✅ BIEN
git commit -m "feat: agregar scripts de migración SQLite a DuckDB"
git commit -m "fix: corregir NULLs en foreign keys de F_Proceso"
git commit -m "data: cargar 19,000 registros SECOP"
git commit -m "docs: agregar README de verificación"

# ❌ MAL
git commit -m "actualización"
git commit -m "cambios"
```

---

## 🌿 Naming de Ramas

```
tipo/descripcion-corta
```

| Prefijo | Uso | Ejemplo |
|---------|-----|---------|
| `feature/` | Nueva funcionalidad | `feature/migracion-duckdb` |
| `fix/` | Corrección de bug | `fix/nulls-foreign-keys` |
| `data/` | Cambios en datos | `data/carga-secop-2024` |
| `docs/` | Documentación | `docs/readme-migracion` |

---

## 📄 Pull Request Template

```markdown
## Descripción
[Cambios realizados]

## Cambios
- [ ] Cambio 1
- [ ] Cambio 2

## Verificación
- [ ] verify_migration.py pasa todas las pruebas

## Issue
Closes #XX
```

---

## 🛡️ Ramas Protegidas

**main:**
- ✅ Requiere PR
- ✅ Requiere 1 aprobación
- ❌ No push directo

---

## 🔧 Comandos Útiles

```bash
git status          # Ver estado
git log --oneline   # Ver commits
git diff            # Ver cambios
git branch -a       # Ver ramas
```

---

*Última actualización: Marzo 2026*
