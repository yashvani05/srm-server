def make_key(key: str, key_prefix: str, version: int) -> str:
    return f"{key_prefix}:{key}"
