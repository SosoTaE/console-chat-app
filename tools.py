import secrets

def generate_secure_user_id(num_bytes=16):
    """
    Generates a cryptographically strong, URL-safe, unique ID for a user.

    This uses the secrets module, which is designed for generating tokens
    for security-sensitive purposes.

    Args:
        num_bytes (int): The number of random bytes to use. More bytes
                         means a longer, more random ID. 16 is a good default.

    Returns:
        str: A URL-safe unique identifier string (e.g., 'pLgVn7yXqZ...').
    """
    return secrets.token_urlsafe(num_bytes)
