#!/usr/bin/env python3

"""
Generate or update .env and .devcontainer/.env from fillme.env

This script supports incremental updates:
- Reads fillme.env and destination files
- Aborts if a field exists in both but differs
- Adds missing fields from fillme.env to destination files
- Generates and adds missing auto-generated fields
"""

import os
import secrets
import sys
from typing import Callable, Dict


def generate_password(length: int = 16) -> str:
    """Generate a random password of specified length"""
    return secrets.token_hex(length // 2)


def generate_name(length: int = 8, prefix: str = "user") -> str:
    """Generate a name with prefix and random suffix"""
    suffix = secrets.token_hex(length // 2)
    return f"{prefix}_{suffix}"


def parse_env_file(filepath: str) -> Dict[str, str]:
    """Parse an env file and return a dict of key-value pairs (ignoring comments)"""
    env_dict: Dict[str, str] = {}
    if not os.path.exists(filepath):
        return env_dict

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                # Сохраняем ключ как есть (потом приведем к верхнему)
                env_dict[key.strip()] = value.strip()

    return env_dict


def get_auto_field_generators() -> Dict[str, Callable[[], str]]:
    """Return a dict of field names to generator functions (ALL UPPERCASE)"""
    return {
        "REDIS_PASSWORD": lambda: generate_password(20),
        "POSTGRES_PASSWORD": lambda: generate_password(24),
        "POSTGRES_USER": lambda: generate_name(12, "postgres"),
        "POSTGRES_DB": lambda: generate_name(10, "duohabbit"),
        "JWT_SECRET": lambda: generate_password(24),
    }


def normalize_env_vars(vars_dict: Dict[str, str]) -> Dict[str, str]:
    """Convert all keys to uppercase"""
    return {key.upper(): value for key, value in vars_dict.items()}


def update_env_file(
    target_file: str,
    fillme_vars: Dict[str, str],
    auto_field_generators: Dict[str, Callable[[], str]],
) -> bool:
    """Update or create an env file incrementally"""
    # Приводим fillme_vars к верхнему регистру
    fillme_vars = normalize_env_vars(fillme_vars)
    
    # Читаем существующий файл и тоже приводим к верхнему
    existing_vars = normalize_env_vars(parse_env_file(target_file))

    # Проверяем конфликты с fillme.env
    for key, value in fillme_vars.items():
        if key in existing_vars and existing_vars[key] != value:
            print(
                f"Error: Field '{key}' exists in {target_file} with a different value"
            )
            print(f"  fillme.env: {key}={value}")
            print(f"  {target_file}: {key}={existing_vars[key]}")
            print("Aborting to prevent conflicts.")
            return False

    # Определяем что нужно добавить
    vars_to_add: Dict[str, str] = {}

    # Добавляем недостающие поля из fillme.env
    for key, value in fillme_vars.items():
        if key not in existing_vars:
            vars_to_add[key] = value

    # Генерируем и добавляем недостающие авто-поля
    for key, generator in auto_field_generators.items():
        if key not in existing_vars:
            vars_to_add[key] = generator()

    # Объединяем
    all_vars = {**existing_vars, **vars_to_add}

    if not vars_to_add:
        print(f"✓ {target_file} is up to date")
        return True

    with open(target_file, "w", encoding="utf-8") as f:
        for key, value in all_vars.items():
            f.write(f"{key}={value}\n")

    if existing_vars:
        print(f"✓ Updated {target_file} with {len(vars_to_add)} new field(s)")
    else:
        print(f"✓ Created {target_file}")

    return True


def main() -> None:
    """Update env files"""
    # Check if fillme.env exists
    if not os.path.exists("fillme.env"):
        print("Error: fillme.env not found in current directory")
        sys.exit(1)

    # Parse fillme.env
    fillme_vars = parse_env_file("fillme.env")

    # Get auto field generators
    auto_field_generators = get_auto_field_generators()

    # Update .env
    if not update_env_file(".env", fillme_vars, auto_field_generators):
        sys.exit(1)

    # Create .devcontainer directory if it doesn't exist
    os.makedirs(".devcontainer", exist_ok=True)

    # Update .devcontainer/.env
    if not update_env_file(".devcontainer/.env", fillme_vars, auto_field_generators):
        sys.exit(1)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()