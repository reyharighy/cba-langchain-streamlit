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

STORE_MANIFEST_STATEMENT = """INSERT INTO manifests (
    manifest_id,
    project_id,
    user_id,
    manifest_no,
    prompt,
    context,
    manifest_file,
    created_at,
    updated_at
)
VALUES (
    :manifest_id,
    :project_id,
    :user_id,
    :manifest_no,
    :prompt,
    :context,
    :manifest_file,
    :created_at,
    :updated_at
)"""

INDEX_MANIFEST_STATEMENT = """SELECT * FROM manifests
WHERE project_id = :project_id
AND user_id = :user_id"""

SHOW_MANIFEST_STATEMENT = """SELECT * FROM manifests
WHERE project_id = :project_id
AND user_id = :user_id
AND manifest_no = :manifest_no"""
