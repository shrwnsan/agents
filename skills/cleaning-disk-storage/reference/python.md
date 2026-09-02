# Python

Python-specific temporary files, caches, and virtual environments.

## Directories

| Pattern | Description | Cleanability |
|---------|-------------|--------------|
| `__pycache__/` | Bytecode cache | Safe |
| `*.pyc`, `*.pyo` | Compiled Python files | Safe |
| `.pytest_cache/` | Pytest cache | Safe |
| `.ruff_cache/` | Ruff linter cache | Safe |
| `.venv/`, `venv/`, `env/` | Virtual environments | Inspect first |
| `*.egg-info/` | Package metadata | Safe |
| `.mypy_cache/` | MyPy type checking cache | Safe |

## Scanning Commands

```bash
# Find __pycache__ directories
find ~ -type d -name "__pycache__"

# Count __pycache__ directories
find ~ -type d -name "__pycache__" | wc -l

# Find .pytest_cache directories
find ~ -type d -name ".pytest_cache"

# Find all Python virtual environments
find ~ -type d \( -name ".venv" -o -name "venv" -o -name "env" \)

# Calculate __pycache__ total size
find ~ -type d -name "__pycache__" -print0 2>/dev/null | xargs -0 du -sk 2>/dev/null | awk '{s+=$1} END {printf "%.1f MB\n", s/1024}'
```

## Notes

- `__pycache__` and `.pyc` files regenerate automatically when running Python scripts
- Virtual environments (`.venv`, `venv`, `env`) require `pip install -r requirements.txt` to restore
- `.pytest_cache` contains test run information that affects pytest behavior
- Active projects should have their virtual environments preserved

## Typical Sizes

- Small project __pycache__: 1-10 MB
- Large project __pycache__: 50-200 MB
- Virtual environment: 100-500 MB (depending on packages)
