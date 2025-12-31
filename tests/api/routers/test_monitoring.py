from unittest import mock

from fastapi import status

from fastpubsub.exceptions import ServiceUnavailable


def test_liveness_probe(client):
    response = client.get("/liveness")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data == {"status": "alive"}


def test_readiness_probe(session, client):
    response = client.get("/readiness")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data == {"status": "ready"}


def test_readiness_probe_with_exception(session, client):
    with mock.patch("fastpubsub.api.routers.monitoring.services.database_ping") as mock_database_ping:
        mock_database_ping.side_effect = [ServiceUnavailable("database is down")]
        response = client.get("/readiness")
        response_data = response.json()

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response_data == {"detail": "database is down"}


def test_prometheus_metrics(client):
    response = client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
