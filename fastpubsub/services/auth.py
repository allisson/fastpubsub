"""Authentication and authorization services for fastpubsub."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from fastpubsub import services
from fastpubsub.config import settings
from fastpubsub.exceptions import InvalidClientToken
from fastpubsub.models import DecodedClientToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/oauth/token", auto_error=False)


def has_scope(token_scopes: set[str], resource: str, action: str, resource_id: str | None = None) -> bool:
    """Check if token scopes include the required permission.

    Evaluates if the provided token scopes grant permission to perform
    the requested action on the specified resource.

    Args:
        token_scopes: Set of scopes from the client's token.
        resource: Resource type (e.g., 'topics', 'subscriptions', 'clients').
        action: Action to perform (e.g., 'create', 'read', 'update', 'delete', 'publish', 'consume').
        resource_id: Optional specific resource ID for fine-grained permissions.

    Returns:
        True if the required scope is granted, False otherwise.
    """
    if "*" in token_scopes:
        return True

    base = f"{resource}:{action}"

    if base in token_scopes:
        return True

    if resource_id and f"{base}:{resource_id}" in token_scopes:
        return True

    return False


async def get_current_token(token: str | None = Depends(oauth2_scheme)) -> DecodedClientToken:
    """Extract and decode the current client's JWT token.

    Args:
        token: OAuth2 bearer token from the request header.

    Returns:
        DecodedClientToken with client ID and scopes.

    Raises:
        InvalidClientToken: If token is invalid or authentication fails.
    """
    if token is None:
        token = ""
    return await services.decode_jwt_client_token(token, auth_enabled=settings.auth_enabled)


def require_scope(resource: str, action: str):
    """Create a dependency that requires specific scope for API endpoints.

    Generates a FastAPI dependency that validates the incoming request
    has the required scope for the specified resource and action.

    Args:
        resource: Resource type (e.g., 'topics', 'subscriptions', 'clients').
        action: Action to perform (e.g., 'create', 'read', 'update', 'delete', 'publish', 'consume').

    Returns:
        FastAPI dependency function that validates scope requirements.

    Raises:
        InvalidClientToken: If client lacks required scope.
    """

    async def dependency(request: Request, token: Annotated[DecodedClientToken, Depends(get_current_token)]):
        resource_id = request.path_params.get("id")
        if resource_id is not None:
            resource_id = str(resource_id)

        if not has_scope(token.scopes, resource, action, resource_id):
            raise InvalidClientToken("Insufficient scope") from None

        return token

    return dependency
