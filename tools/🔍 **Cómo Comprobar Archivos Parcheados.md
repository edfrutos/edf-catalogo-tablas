## 🔍 **Cómo Comprobar Archivos Parcheados por Merges de Git**

Te muestro varias formas de detectar archivos que han sido modificados por merges de Git:

### 📋 **1. Verificar el estado actual de Git:**

```bash
git status
```
### 🔍 **2. Verificar el historial de merges:**

```bash
git log --merges --oneline -10
```
### 🔍 **3. Ver archivos modificados en el último merge:**

```bash
git show --name-only --pretty=format:"" 3a47811
```
### 🔍 **4. Ver diferencias entre ramas:**

```bash
git diff --name-only master..IDE_Trae 2>/dev/null || echo "Rama IDE_Trae no encontrada"
```
### 🔍 **5. Verificar archivos con conflictos de merge recientes:**

```bash
git log --grep="Merge" --oneline -5
```
### 🔍 **6. Ver archivos modificados en el merge con conflictos:**

```bash
git show --name-only --pretty=format:"" fd8a54a
```
### 🔍 **7. Crear script para detectar archivos parcheados:**

### 🔍 **8. Ejecutar el script de detección:**

```bash
source venv310/bin/activate && python tools/detect_merge_files.py
```
### 🔍 **9. Verificar archivos con conflictos de merge:**

```bash
git status --porcelain | grep -E "^[UAD]"
```
### 🔍 **10. Verificar archivos con marcadores de conflicto:**

```bash
grep -r "<<<<<<< HEAD" . --exclude-dir=.git --exclude-dir=venv310 --exclude-dir=__pycache__ 2>/dev/null | head -5
```
### 🔍 **11. Verificar archivo con conflictos:**

Read file: docs/README.md
### 🔧 **12. Corregir archivo con conflictos:**

### 🔍 **13. Verificar que no hay más conflictos:**

```bash
grep -r "<<<<<<< HEAD" . --exclude-dir=.git --exclude-dir=venv310 --exclude-dir=__pycache__ 2>/dev/null
```
### 🔍 **14. Ejecutar script de detección final:**

```bash
source venv310/bin/activate && python tools/detect_merge_files.py
```
## ✅ **Resumen: Cómo Comprobar Archivos Parcheados por Merges de Git**

### 🔍 **Métodos de Detección:**

#### **1. Comandos Git Básicos:**
```bash
# Ver estado actual
git status

# Ver historial de merges
git log --merges --oneline

# Ver archivos modificados en un merge específico
git show --name-only --pretty=format: "" <commit_hash>

# Ver diferencias entre ramas
git diff --name-only <rama1>..<rama2>
```

#### **2. Detectar Conflictos Actuales:**
```bash
# Ver archivos con conflictos
git status --porcelain | grep -E "^[UAD]"

# Buscar marcadores de conflicto
grep -r "<<<<<<< HEAD" . --exclude-dir=.git
grep -r "=======" . --exclude-dir=.git
grep -r ">>>>>>>" . --exclude-dir=.git
```

#### **3. Script Automatizado:**
- **Creado**: `tools/detect_merge_files.py`
- **Funcionalidades**:
  - Detecta conflictos de merge actuales
  - Analiza historial de merges
  - Muestra archivos modificados por tipo
  - Identifica archivos más frecuentemente modificados

### 📊 **Resultados del Análisis:**

#### **✅ Estado Actual:**
- **2 commits de merge** detectados
- **0 archivos con conflictos** activos
- **1 archivo corregido**: `docs/README.md` (marcadores de conflicto eliminados)

#### **⚠️ Archivos Eliminados:**
- `.cspell.json` (consolidado en `pyproject.toml`)
- `.eslintignore` (consolidado en `pyproject.toml`)
- `.flake8` (consolidado en `pyproject.toml`)

### 🔧 **Herramientas Creadas:**

1. **`tools/detect_merge_files.py`**:
   - Análisis completo de merges
   - Detección de conflictos
   - Estadísticas de archivos modificados
   - Reporte detallado por commit

### 🎯 **Recomendaciones:**

1. **Ejecutar regularmente** el script de detección
2. **Revisar conflictos** antes de hacer commits
3. **Usar el script** para auditorías de código
4. **Mantener limpio** el historial de Git

### ✅ **Estado Final:**
- **Sin conflictos de merge** activos
- **Sin marcadores de conflicto** en archivos
- **Herramienta de detección** disponible
- **Documentación actualizada** y limpia

¡Tu repositorio está ahora libre de conflictos de merge! 🎯