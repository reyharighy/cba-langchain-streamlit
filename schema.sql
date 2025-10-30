CREATE TABLE IF NOT EXISTS projects (
    project_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    title TEXT,
    dataset_dir TEXT NOT NULL,
    dataset_file TEXT NOT NULL,
    manifest_dir TEXT NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manifests (
    manifest_id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    manifest_no INT NOT NULL,
    prompt TEXT NOT NULL,
    context TEXT NOT NULL,
    manifest_file TEXT NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_manifests_project_id_user_id
ON manifests (project_id, user_id, created_at ASC);

CREATE INDEX idx_manifests_project_id_user_id_manifest_no
ON manifests (project_id, user_id, manifest_no);
