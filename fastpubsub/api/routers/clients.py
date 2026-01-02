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
    await services.delete_client(id)


@router.post(
    "/oauth/token",
    response_model=models.ClientToken,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a new client token",
)
async def issue_client_token(data: models.IssueClientToken):
    return await services.issue_jwt_client_token(client_id=data.client_id, client_secret=data.client_secret)
