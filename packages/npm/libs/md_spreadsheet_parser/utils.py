def normalize_header(header: str) -> str:
    """
    Normalizes a header string to match field names (lowercase, snake_case).
    Example: "User Name" -> "user_name"
    """
    return header.lower().replace(" ", "_").strip()
