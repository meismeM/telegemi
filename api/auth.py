from .config import ALLOWED_USERS,ADMIN_ID,AUCH_ENABLE


def is_authorized(from_id: int, user_name: str) -> bool:
    if AUCH_ENABLE == "0": # String comparison as env vars are strings
        return True
    # Ensure ALLOWED_USERS contains strings for comparison
    allowed_users_lower = [str(u).lower() for u in ALLOWED_USERS]
    if str(user_name).lower() in allowed_users_lower or str(from_id) in allowed_users_lower:
        return True
    return False


def is_admin(from_id: int) -> bool:
    if str(from_id) == ADMIN_ID: # String comparison
        return True
    return False
