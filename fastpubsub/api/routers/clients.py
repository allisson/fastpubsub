"""API endpoints for client management operations."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from fastpubsub import models, services

router = APIRouter(tags=["clients"])


@router.post(
    "/clients",
    response_model=models.CreateClientResult,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
)
async def create_client(
    data: models.CreateClient,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("clients", "create"))],
):
    """Create a new client with specified name and scopes.

    Creates a new authorized client that can access the pub/sub API
    based on their granted scopes. Returns the client ID and generated secret.

    Args:
        data: Client creation data including name, scopes, and active status.
        token: Decoded client token with 'clients:create' scope.

    Returns:
        CreateClientResult containing the new client ID and secret.

    Raises:
        AlreadyExistsError: If a client with the same ID already exists.
        InvalidClient: If the requesting client lacks 'clients:create' scope.
    """
    return await services.create_client(data)


@router.get(
    "/clients/{id}",
    response_model=models.Client,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.GenericError}},
    summary="Get a client",
)
async def get_client(
    id: uuid.UUID,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("clients", "read"))],
):
    """Retrieve a client by ID.

    Returns the full details of an existing client including ID, name,
    scopes, status, and timestamps.

    Args:
        id: UUID of the client to retrieve.
        token: Decoded client token with 'clients:read' scope.

    Returns:
        Client model with full client details.

    Raises:
        NotFoundError: If no client with the given ID exists.
        InvalidClient: If the requesting client lacks 'clients:read' scope.
    """
    return await services.get_client(id)


@router.put(
    "/clients/{id}",
    response_model=models.Client,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.GenericError}},
    summary="Update a client",
)
async def update_client(
    id: uuid.UUID,
    data: models.UpdateClient,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("clients", "update"))],
):
    """Update an existing client's name, scopes, or active status.

    Modifies the properties of an existing client. Only the fields
    provided in the update data will be modified.

    Args:
        id: UUID of the client to update.
        data: Updated client data including name, scopes, and/or active status.
        token: Decoded client token with 'clients:update' scope.

    Returns:
        Client model with updated details.

    Raises:
        NotFoundError: If no client with the given ID exists.
        InvalidClient: If the requesting client lacks 'clients:update' scope.
    """
    return await services.update_client(id, data)


@router.get(
    "/clients",
    response_model=models.ListClientAPI,
    status_code=status.HTTP_200_OK,
    summary="List clients",
)
async def list_client(
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("clients", "read"))],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    """List clients with pagination support.

    Returns a paginated list of all clients in the system.

    Args:
        token: Decoded client token with 'clients:read' scope.
        offset: Number of items to skip (for pagination).
        limit: Maximum number of items to return (1-100).

    Returns:
        ListClientAPI containing the list of clients.

    Raises:
        InvalidClient: If the requesting client lacks 'clients:read' scope.
    """
    clients = await services.list_client(offset, limit)
    return models.ListClientAPI(data=clients)


@router.delete(
    "/clients/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.GenericError}},
    summary="Delete a client",
)
async def delete_client(
    id: uuid.UUID,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("clients", "delete"))],
):
    """Delete a client by ID.

    Permanently removes a client from the system. This action cannot be undone.

    Args:
        id: UUID of the client to delete.
        token: Decoded client token with 'clients:delete' scope.

    Raises:
        NotFoundError: If no client with the given ID exists.
        InvalidClient: If the requesting client lacks 'clients:delete' scope.
    """
    await services.delete_client(id)


@router.post(
    "/oauth/token",
    response_model=models.ClientToken,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a new client token",
)
async def issue_client_token(data: models.IssueClientToken):
    """Issue a new JWT access token for a client.

    Generates a new access token that the client can use for authentication
    in subsequent API requests. The token includes the client's scopes
    and has an expiration time.

    Args:
        data: Client credentials including ID and secret for authentication.

    Returns:
        ClientToken containing the access token, type, expiration, and scopes.

    Raises:
        InvalidClient: If client ID or secret is invalid.
        ServiceUnavailable: If token generation service is unavailable.
    """
    return await services.issue_jwt_client_token(client_id=data.client_id, client_secret=data.client_secret)
