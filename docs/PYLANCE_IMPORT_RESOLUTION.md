# Resolving Pylance Import Resolution Warnings

This guide addresses the common issue where Pylance reports "Import could not be resolved" for packages that are properly installed and working at runtime.

## Problem Statement

- **Symptom**: Pylance shows red squiggly lines under imports (e.g., `import pdfplumber`)
- **Message**: "Import 'pdfplumber' could not be resolved"
- **Context**: Packages are confirmed installed (`pip list` shows them) and runtime tests pass

## Root Cause

Pylance uses a separate type-checking Python environment that may differ from your runtime environment. This is a VS Code/Pylance configuration issue, not a code problem.

## Step-by-Step Resolution

### Step 1: Verify Python Interpreter Selection

1. Open VS Code Command Palette: `Ctrl+Shift+P`
2. Type: `Python: Select Interpreter`
3. Choose the interpreter that has the packages installed:
   ```
   C:\Program Files\Python311\python.exe
   ```
4. Look for ✓ (checkmark) indicating the active interpreter

**Verification**: Run in terminal:
```cmd
where python
"C:\Program Files\Python311\python.exe" -c "import pdfplumber; print('pdfplumber OK')"
```

### Step 2: Restart Pylance Language Server

1. Open VS Code Command Palette: `Ctrl+Shift+P`
2. Type: `Python: Restart Language Server`
3. Wait for restart to complete (status bar shows "Pylance" or "Python")

### Step 3: Clear Pylance Cache

1. Close VS Code completely
2. Delete the cache folder:
   ```cmd
   rmdir /s /q %USERPROFILE%\.cache\pylance
   ```
3. Delete any `.pyright` folder in your workspace
4. Reopen VS Code

### Step 4: Verify Workspace Settings

Check or create `.vscode/settings.json` in your workspace:

```json
{
    "python.pythonPath": "C:\\Program Files\\Python311\\python.exe",
    "python.analysis.extraPaths": [
        "C:\\Program Files\\Python311\\lib\\site-packages"
    ],
    "python.analysis.typeCheckingMode": "basic",
    "python.autoComplete.extraPaths": [
        "C:\\Program Files\\Python311\\lib\\site-packages"
    ]
}
```

### Step 5: Configure Pylance for Current Workspace

In `.vscode/settings.json`, add:

```json
{
    "python.analysis.diagnosticMode": "workspace",
    "python.analysis.autoImportCompletions": true,
    "python.analysis.completeFunctionParens": true
}
```

### Step 6: Reinstall Packages (Force Re-link)

```cmd
"C:\Program Files\Python311\python.exe" -m pip uninstall pdfplumber PyPDF2 beautifulsoup4 lxml -y
"C:\Program Files\Python311\python.exe" -m pip install pdfplumber PyPDF2 beautifulsoup4 lxml
```

### Step 7: Verify PYTHONPATH Environment Variable

Check if PYTHONPATH is set correctly:
```cmd
echo %PYTHONPATH%
```

If empty or incorrect, set it:
```cmd
set PYTHONPATH=C:\Program Files\Python311\Lib\site-packages
```

Or permanently via System Properties → Environment Variables.

### Step 8: Check Virtual Environments

If using a virtual environment (venv):
1. Activate it: `.\venv\Scripts\activate`
2. Install packages in venv: `pip install pdfplumber PyPDF2 beautifulsoup4 lxml`
3. Select venv interpreter in VS Code

## Advanced Troubleshooting

### Option A: Use Pyright Configuration File

Create `pyrightconfig.json` in workspace root:
```json
{
    "venvPath": ".",
    "venv": "venv"
}
```

### Option B: Disable Specific Diagnostic (Temporary)

Add to `.vscode/settings.json`:
```json
{
    "python.analysis.diagnosticSettings": {
        "typeCheckingMode": "off"
    }
}
```

**Warning**: This disables all type checking, not recommended for production.

### Option C: Add Stub Files (Fallback)

Create `typings/pdfplumber.pyi`:
```python
from typing import Any

def open(path: str) -> Any: ...
```

## Verification Checklist

After applying fixes, verify:

- [ ] `Ctrl+Shift+P` → "Python: Select Interpreter" shows correct path
- [ ] Terminal shows packages: `pip list | findstr pdfplumber`
- [ ] Runtime test passes: `python test_imports.py`
- [ ] Pylance imports show no red squiggly lines
- [ ] IntelliSense works for imported modules

## Quick Commands Reference

| Action | Command |
|--------|---------|
| Check Python path | `where python` |
| Check packages | `pip list \| findstr -i "pdfplumber"` |
| Test import | `python -c "import pdfplumber; print('OK')"` |
| Restart LSP | `Ctrl+Shift+P` → "Python: Restart Language Server" |
| Clear cache | Delete `%USERPROFILE%\.cache\pylance` |

## Summary

The Pylance warnings are **not code errors** - they're IDE configuration issues. The resolution sequence is:

1. **Select correct interpreter** (most common fix)
2. **Restart language server**
3. **Clear Pylance cache**
4. **Configure workspace settings**
5. **Reinstall packages** if needed

Once configured correctly, Pylance will recognize the installed packages and the warnings will disappear.
