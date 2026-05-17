# SharedMemoryIPC Project Guide

This document defines core commands, code styling, and development policies for the SharedMemoryIPC project.

## 🛠️ Commands

### 1. Verification & Tests
Run simulation tests and driver verification:
```powershell
# Run the main IPC simulation test
python -m unittest tests/test_shm_ipc_260517.py

# Alternatively, run via direct script execution
python tests/test_shm_ipc_260517.py
```

### 2. Lint & Code Quality
Use Ruff for fast Python linting and formatting:
```powershell
# Check code style and rules
ruff check .

# Fix auto-fixable lint errors
ruff check . --fix

# Format code using Black-compatible formatter
ruff format .
```

---

## 🎨 Code Style

### 1. Code Standards (PEP 8)
- **Formatting**: Limit all lines to a maximum of 100 characters. Use 4 spaces for indentation.
- **Naming Conventions**:
  - Classes: `PascalCase` (e.g., `SharedMemoryIPCDriver`)
  - Functions & Variables: `snake_case` (e.g., `write_message`, `read_index`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_BUFFER_SIZE`)
- **Type Annotations**: Always include type hints for public methods and complex function parameters to guarantee safety.

### 2. Low-Level Resource & Error Safety
- **No Silent Resource Leaks**: Always use `try...finally` or context managers (`with` statements) to clean up shared memory mappings, locks, and file descriptors.
- **Explicit Exceptions**: Avoid generic exceptions. Raise domain-specific exceptions (e.g., `SharedMemoryIPCLockError`, `SharedMemoryIPCBufferOverflow`) to allow calling agents to react appropriately.

---

## 📝 Debugging Notes Policy
Substantive changes to code or documentation must be recorded in `docs/debugging_notes.md`.
- Keep the log concise (approx. 5 lines per entry).
- Document in **reverse chronological order** (newest-first).
- Required fields: `when`, `topic`, `change`, `test`, `evidence`, `next`.
