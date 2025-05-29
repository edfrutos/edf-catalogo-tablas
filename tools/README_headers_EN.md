# Python Script Header Standardization (Quick Guide)

## Why?
A standard header in every Python script makes your codebase easier to understand, maintain, and collaborate on. Anyone can quickly see what a script does, how to use it, and who wrote it.

---

## 1. Header Template
Always use the template in `tools/plantilla_cabecera_script.py` when creating a new script. Fill in the fields before you start coding.

**Header example:**
```python
# Script: SCRIPT_NAME.py
# Description: [Briefly explain what the script does]
# Usage: python3 SCRIPT_NAME.py [options]
# Requires: [external libraries, if any]
# Environment variables: [if any]
# Author: [Your name or team] - [Date]
```

---

## 2. Automation: Script & Pre-commit Hook

### a) Apply headers to all scripts
From the project root, run:
```bash
python3 tools/aplicar_cabecera_todos.py
```
This will check all `.py` scripts (except those in venv, .git, and site-packages) and add the standard header if missing.

### b) Pre-commit hook
The `.git/hooks/pre-commit` hook automatically applies the header to all Python scripts before every commit. You never forget to document a script!

---

## 3. Best Practices
- **Never skip the header, even for small or test scripts.**
- **Update the header if the script's purpose changes.**
- **Share this standard with your team.**
- **Include this step in your code review checklist.**

---

## 4. Typical workflow
1. Create a new script from the template:
   ```bash
   cp tools/plantilla_cabecera_script.py tools/my_new_script.py
   # Edit and fill in the header
   ```
2. Before committing, make sure all scripts have a header:
   ```bash
   python3 tools/aplicar_cabecera_todos.py
   # or just git commit and the hook will do it for you
   ```

---

## 5. Questions or suggestions?
If you have ideas to improve the template or workflow, share them with the team. 