# Phase 4: Code Implementation

**Make code match documentation exactly**

---

## Goal

Implement code that matches documentation specification exactly. Code follows docs, not the other way around.

**Philosophy reminder**: If implementation needs to differ, update docs first (with approval).

---

## General Principles

1. **Code follows docs exactly** - No deviation without doc update
2. **Load full context first** - Read all related files before coding
3. **Implement in phases** - Smaller chunks, test as you go
4. **Use [file crawling](../core_concepts/file_crawling.md)** - For large changes
5. **PAUSE on conflicts** - Don't guess, ask user
6. **Commit incrementally** - Logical feature groupings

---

## File Crawling for Code Changes

For large-scale changes:

```bash
# Generate code file index
cat > /tmp/code_to_implement.txt << 'EOF'
[ ] amplifier-core/amplifier_core/config/provider_manager.py
[ ] amplifier-core/amplifier_core/config/module_manager.py
[ ] amplifier-app-cli/amplifier_app_cli/commands/init.py
[ ] amplifier-app-cli/amplifier_app_cli/commands/provider.py
