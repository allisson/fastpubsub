"""Client management services for authentication and authorization."""

import datetime
import secrets
import uuid

from jose import jwt
from jose.exceptions import JWTError
from pwdlib import PasswordHash
from sqlalchemy import select

from fastpubsub.config import settings
from fastpubsub.database import Client as DBClient
from fastpubsub.database import SessionLocal
from fastpubsub.exceptions import InvalidClient
from fastpubsub.models import (
    Client,
    ClientToken,
    CreateClient,
    CreateClientResult,
    DecodedClientToken,
    UpdateClient,
)
from fastpubsub.services.helpers import _delete_entity, _get_entity, utc_now

password_hash = PasswordHash.recommended()


def generate_secret() -> str:
    """Generate a cryptographically secure random secret.

    Creates a random 32-character hexadecimal string that can be used
    as a client secret for JWT token authentication.

    Returns:
        Random secret string in hexadecimal format.
    """
    return secrets.token_hex(16)


async def create_client(data: CreateClient) -> CreateClientResult:
    """Create a new client with authentication credentials.

    Creates a new client in the database with a generated secret and
    initializes the client with the provided configuration.

    Args:
        data: Client creation data including name, scopes, and active status.

    Returns:
        CreateClientResult containing the new client ID and generated secret.

    Raises:
        AlreadyExistsError: If a client with the same ID already exists.
        ValueError: If client data validation fails.
    """
    async with SessionLocal() as session:
        now = utc_now()
        secret = generate_secret()
        secret_hash = password_hash.hash(secret)
        db_client = DBClient(
            id=uuid.uuid7(),
            name=data.name,
            scopes=data.scopes,
            is_active=data.is_active,
            secret_hash=secret_hash,
            token_version=1,
            created_at=now,
            updated_at=now,
        )
        session.add(db_client)

        await session.commit()

    return CreateClientResult(id=db_client.id, secret=secret)


async def get_client(client_id: uuid.UUID) -> Client:
    """Retrieve a client by ID.

    Fetches the full details of an existing client from the database.

    Args:
        client_id: UUID of the client to retrieve.

    Returns:
        Client model with full client details.

    Raises:
        NotFoundError: If no client with the given ID exists.
    """
    async with SessionLocal() as session:
        db_client = await _get_entity(session, DBClient, client_id, "Client not found")

    return Client(**db_client.to_dict())


async def list_client(offset: int, limit: int) -> list[Client]:
    """List clients with pagination support.

    Retrieves a paginated list of all clients in the system.

    Args:
        offset: Number of items to skip for pagination.
        limit: Maximum number of items to return.

    Returns:
        List of Client models.
    """
    async with SessionLocal() as session:
        stmt = select(DBClient).order_by(DBClient.id.asc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        db_clients = result.scalars().all()

    return [Client(**db_client.to_dict()) for db_client in db_clients]


async def update_client(client_id: uuid.UUID, data: UpdateClient) -> Client:
    """Update an existing client's properties.

    Modifies the properties of an existing client and increments
    the token version to invalidate existing tokens.

    Args:
        client_id: UUID of the client to update.
        data: Updated client data including name, scopes, and active status.

    Returns:
        Client model with updated details.

    Raises:
        NotFoundError: If no client with the given ID exists.
    """
    async with SessionLocal() as session:
        db_client = await _get_entity(session, DBClient, client_id, "Client not found")
        db_client.name = data.name
        db_client.scopes = data.scopes
        db_client.is_active = data.is_active
        db_client.token_version += 1
        db_client.updated_at = utc_now()

        await session.commit()

    return Client(**db_client.to_dict())


async def delete_client(client_id: uuid.UUID) -> None:
    """Delete a client by ID.

    Permanently removes a client from the database and all associated data.

    Args:
        client_id: UUID of the client to delete.

    Raises:
        NotFoundError: If no client with the given ID exists.
    """
    async with SessionLocal() as session:
        await _delete_entity(session, DBClient, client_id, "Client not found")


async def issue_jwt_client_token(client_id: uuid.UUID, client_secret: str) -> ClientToken:
    """Issue a new JWT access token for a client.

    Validates client credentials and generates a new access token
    with the client's scopes and expiration time.

    Args:
        client_id: UUID of the client requesting a token.
        client_secret: Client's secret for authentication.

    Returns:
        ClientToken containing the access token, expiration, and scopes.

    Raises:
        InvalidClient: If client credentials are invalid or client is disabled.
    """
    async with SessionLocal() as session:
        db_client = await _get_entity(session, DBClient, client_id, "Client not found", raise_exception=False)
        if not db_client:
            raise InvalidClient("Client not found") from None
        if not db_client.is_active:
            raise InvalidClient("Client disabled") from None
        if password_hash.verify(client_secret, db_client.secret_hash) is False:
            raise InvalidClient("Client secret is invalid") from None

        now = utc_now()
        expires_in = now + datetime.timedelta(minutes=settings.auth_access_token_expire_minutes)
        payload = {
            "sub": str(client_id),
            "exp": expires_in,
            "iat": now,
            "scope": db_client.scopes,
            "ver": db_client.token_version,
        }
        access_token = jwt.encode(payload, key=settings.auth_secret_key, algorithm=settings.auth_algorithm)

    return ClientToken(
        access_token=access_token,
        expires_in=int((expires_in - now).total_seconds()),
        scope=db_client.scopes,
    )


async def decode_jwt_client_token(access_token: str, auth_enabled: bool = True) -> DecodedClientToken:
    """Decode and validate a JWT access token.

    Validates the token signature, expiration, and client status.
    Ensures the token hasn't been revoked by checking token version.

    Args:
        access_token: JWT access token to decode and validate.
        auth_enabled: Whether authentication is enabled (for testing).

    Returns:
        DecodedClientToken with client ID and scopes.

    Raises:
        InvalidClient: If token is invalid, expired, or client is disabled/revoked.
    """
    if not auth_enabled:
        return DecodedClientToken(client_id=uuid.uuid7(), scopes={"*"})

    try:
        payload = jwt.decode(
            access_token,
            key=settings.auth_secret_key,
            algorithms=[settings.auth_algorithm],
        )
    except JWTError:
        raise InvalidClient("Invalid jwt token") from None

    client_id = payload["sub"]
    scopes = payload["scope"]
    token_version = payload["ver"]

    async with SessionLocal() as session:
        db_client = await _get_entity(session, DBClient, client_id, "Client not found", raise_exception=False)
        if not db_client:
            raise InvalidClient("Client not found") from None
        if not db_client.is_active:
            raise InvalidClient("Client disabled") from None
        if token_version != db_client.token_version:
            raise InvalidClient("Token revoked") from None

    return DecodedClientToken(client_id=uuid.UUID(client_id), scopes={scope for scope in scopes.split()})
