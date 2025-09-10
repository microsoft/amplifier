# PostgreSQL Support Removed

**Date:** September 10, 2025  
**Reason:** PostgreSQL was never used; all storage is file-based

## Summary

PostgreSQL and Azure database infrastructure have been removed from the codebase following the philosophy of ruthless simplicity. Analysis revealed that no code in the amplifier modules actually used PostgreSQL - all storage is file-based using JSON/JSONL files in the `.data/` directory.

## What Was Removed

### Dependencies
- `psycopg2-binary` from `pyproject.toml`

### Directories
- `/db_setup/` - Complete PostgreSQL setup module
- `/infrastructure/azure/` - Azure PostgreSQL scripts and Bicep templates

### Documentation
- `docs/AZURE_POSTGRESQL_SETUP.md`
- `docs/AZURE_POSTGRESQL_MANAGED_IDENTITY.md`
- `docs/AZURE_POSTGRESQL_AUTOMATION.md`

### Configuration
- DATABASE_URL section from `.env.example`
- Azure and database make targets from `Makefile` (azure-create, azure-teardown, setup-db, etc.)

## Current Storage Approach

All modules continue to use file-based storage:

- **Knowledge System**: `.data/knowledge/` (JSON/JSONL files)
- **Memory System**: `.data/memory.json`
- **Claude Web**: SQLite (Python standard library, no external database)

## Impact

**Zero functional impact** - The system continues to work exactly as before since PostgreSQL was never actually used.

## Verification

After removal, all checks pass:
- `make check` - All linting, formatting, and type checking passes
- No remaining references to `psycopg2`, `db_setup`, or PostgreSQL configuration
- Knowledge system and all amplifier modules continue functioning normally

## Philosophy Alignment

This removal aligns with the project's implementation philosophy:
- **Ruthless Simplicity**: Removed ~500 lines of unused code
- **YAGNI Principle**: Eliminated hypothetical future database support
- **File-Based Storage**: Maintains the simplest working solution