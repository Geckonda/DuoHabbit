"""Invite-code generation for groups."""

import secrets


def generate_invite_code(length_bytes: int = 4) -> str:
    """Generate a short, URL-safe invite code (default: 8 hex chars)."""
    return secrets.token_hex(length_bytes)
