"""Entry point for auth service CLI — invoked as ``python -m auth.cli``.

Supports subcommands for administrative operations that are not exposed
via the HTTP API (e.g. pre-seeding accounts, rotating keys).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import NoReturn

from sqlalchemy import select

from auth.models.user import User, UserRole
from auth.services.password import hash_password
from storage.config import settings
from storage.db import get_session


def _fail(msg: str) -> NoReturn:
    """Print an error message to stderr and exit with code 1."""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


async def _seed_sahayak() -> None:
    """Create the pre-seeded Sahayak account if it does not already exist.

    Reads credentials from ``storage.config.settings`` (populated from
    ``SAHAYAK_EMAIL`` / ``SAHAYAK_PASSWORD`` environment variables or
    ``.env``).  Exits cleanly with code 0 whether the user is created or
    already present.
    """
    email = settings.SAHAYAK_EMAIL
    password = settings.SAHAYAK_PASSWORD

    if not email:
        _fail("SAHAYAK_EMAIL is not set — check your .env file or environment")
    if not password:
        _fail("SAHAYAK_PASSWORD is not set — check your .env file or environment")

    async with get_session()() as session:
        # Check for existing Sahayak user (idempotency guard).
        result = await session.execute(
            select(User).where(User.email == email),
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            print(f"Sahayak account already exists: {email}")
            return

        # Create and persist the new user.
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.sahayak,
            is_active=True,
            email_verified=True,
        )
        session.add(user)
        await session.commit()

    print(f"Sahayak account created: {email}")


def main(argv: list[str] | None = None) -> None:
    """Parse argv and dispatch to the appropriate subcommand handler.

    Accepts ``argv`` so that tests can pass ``["seed-sahayak"]`` without
    needing to patch ``sys.argv`` directly.
    """
    parser = argparse.ArgumentParser(
        prog="python -m auth.cli",
        description="Auth service administration CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # -- seed-sahayak ----------------------------------------------------------
    subparsers.add_parser(
        "seed-sahayak",
        help="Pre-seed the Sahayak account (idempotent)",
    )

    args = parser.parse_args(argv)

    if args.subcommand == "seed-sahayak":
        asyncio.run(_seed_sahayak())
    else:
        _fail(f"Unknown subcommand: {args.subcommand}")


if __name__ == "__main__":
    main()
