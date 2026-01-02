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
    return secrets.token_hex(16)


async def create_client(data: CreateClient) -> CreateClientResult:
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
    async with SessionLocal() as session:
        db_client = await _get_entity(session, DBClient, client_id, "Client not found")

    return Client(**db_client.to_dict())


async def list_client(offset: int, limit: int) -> list[Client]:
    async with SessionLocal() as session:
        stmt = select(DBClient).order_by(DBClient.id.asc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        db_clients = result.scalars().all()

    return [Client(**db_client.to_dict()) for db_client in db_clients]


async def update_client(client_id: uuid.UUID, data: UpdateClient) -> Client:
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
    async with SessionLocal() as session:
        await _delete_entity(session, DBClient, client_id, "Client not found")


async def issue_jwt_client_token(client_id: uuid.UUID, client_secret: str) -> ClientToken:
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

    return DecodedClientToken(
        client_id=uuid.UUID(client_id), scopes={scope for scope in scopes.split()}
    )
