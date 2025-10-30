# Project Data: Manifests

This directory stores the **runtime artifacts** generated during application execution.

## Purpose

- Implements the **manifest** of each interaction turn using the Streamlit API reference.  
- Each file is created in the format:

  ```text
  manifest_1.py
  manifest_2.py
  manifest_3.py
  ...
  ```

- Files are automatically synced with the **manifests record** in PostgreSQL.

## Usage Notes

- Files are generated and updated automatically at runtime.  
- Do **not** modify files manually, as they may become unsynced with the database.  
- You may safely delete all files in this directory **only if** the PostgreSQL container’s volume is pruned or reset.  
- Otherwise, leave the contents as-is.
