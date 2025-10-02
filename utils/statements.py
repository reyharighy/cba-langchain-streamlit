"""Store all statements used to query ORM models."""

STORE_PROJECT_STATEMENT = """INSERT INTO projects (
    project_id,
    user_id,
    title,
    dataset_dir,
    dataset_file,
    manifest_dir,
    created_at,
    updated_at
)
VALUES (
    :project_id,
    :user_id,
    :title,
    :dataset_dir,
    :dataset_file,
    :manifest_dir,
    :created_at,
    :updated_at
)"""

SHOW_PROJECT_STATEMENT = """SELECT * FROM projects
WHERE project_id = :project_id"""

STORE_PROMPT_MANIFEST_STATEMENT = """INSERT INTO prompt_manifests (
    prompt_manifest_id,
    project_id,
    user_id,
    prompt_manifest_no,
    prompt,
    context,
    manifest_file,
    created_at,
    updated_at
)
VALUES (
    :prompt_manifest_id,
    :project_id,
    :user_id,
    :prompt_manifest_no,
    :prompt,
    :context,
    :manifest_file,
    :created_at,
    :updated_at
)"""

INDEX_PROMPT_MANIFEST_STATEMENT = """SELECT * FROM prompt_manifests
WHERE project_id = :project_id
AND user_id = :user_id"""

SHOW_PROMPT_MANIFEST_STATEMENT = """SELECT * FROM prompt_manifests
WHERE project_id = :project_id
AND user_id = :user_id
AND prompt_manifest_no = :prompt_manifest_no"""
