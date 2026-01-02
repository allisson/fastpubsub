from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from fastpubsub import services
from fastpubsub.config import settings
from fastpubsub.exceptions import InvalidClientToken
from fastpubsub.models import DecodedClientToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/oauth/token", auto_error=False)


def has_scope(token_scopes: set[str], resource: str, action: str, resource_id: str | None = None) -> bool:
    if "*" in token_scopes:
        return True

    base = f"{resource}:{action}"

    if base in token_scopes:
        return True

    if resource_id and f"{base}:{resource_id}" in token_scopes:
        return True

    return False


async def get_current_token(token: str | None = Depends(oauth2_scheme)) -> DecodedClientToken:
    if token is None:
        token = ""
    return await services.decode_jwt_client_token(token, auth_enabled=settings.auth_enabled)


def require_scope(resource: str, action: str):
    async def dependency(request: Request, token: Annotated[DecodedClientToken, Depends(get_current_token)]):
        resource_id = request.path_params.get("id")
        if resource_id is not None:
            resource_id = str(resource_id)

        if not has_scope(token.scopes, resource, action, resource_id):
            raise InvalidClientToken("Insufficient scope") from None

        return token

    return dependency
