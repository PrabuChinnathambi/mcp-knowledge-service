class AccessDeniedError(Exception):
    pass


# Multi-tenant user mapping for POC. Connect to OIDC/OAuth in production.
USER_DIRECTORY = {
    "alice": {"role": "admin", "workspaces": ["hr-docs", "api-docs", "engineering"]},
    "bob": {"role": "viewer", "workspaces": ["api-docs"]},
    "charlie": {"role": "editor", "workspaces": ["engineering"]},
}


def assert_workspace_access(user_id: str, workspace_id: str):
    user_record = USER_DIRECTORY.get(user_id)
    if not user_record or workspace_id not in user_record["workspaces"]:
        raise AccessDeniedError(f"User '{user_id}' is not authorized to access workspace '{workspace_id}'")


def assert_can_write(user_id: str, workspace_id: str):
    assert_workspace_access(user_id, workspace_id)
    role = USER_DIRECTORY[user_id]["role"]
    if role not in {"admin", "editor"}:
        raise AccessDeniedError(f"User '{user_id}' lacks write permissions for workspace '{workspace_id}'")

