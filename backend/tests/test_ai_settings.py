from contextlib import asynccontextmanager

import httpx
import pytest

from bibi.main import create_app


class MemoryCredentials:
    def __init__(self):
        self.value = None
        self.fail_write = False
        self.writes = 0
        self.deletes = 0

    @property
    def available(self):
        return True

    def get(self):
        return self.value

    def set(self, value):
        self.writes += 1
        if self.fail_write:
            raise RuntimeError("secure store unavailable")
        self.value = value

    def delete(self):
        self.deletes += 1
        self.value = None

@asynccontextmanager
async def api(credentials=None):
    credential_store = credentials or MemoryCredentials()
    app = create_app(credential_store=credential_store)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1",
        ) as client:
            yield client, credential_store


async def test_settings_save_replace_and_delete_never_returns_key():
    secret = "sk-or-v1-" + "x" * 40
    async with api() as (client, store):
        initial = await client.get("/api/v1/ai/settings")
        assert initial.status_code == 200
        assert initial.json() == {
            "hasKey": False,
            "selectedModelId": None,
            "storeStatus": "available",
        }

        saved = await client.put("/api/v1/ai/settings", json={"apiKey": secret})
        assert saved.status_code == 200
        assert saved.json()["hasKey"] is True
        assert secret not in saved.text
        assert secret not in (await client.get("/api/v1/ai/settings")).text
        assert store.value == secret

        replacement = "sk-or-v1-" + "y" * 40
        assert (await client.put("/api/v1/ai/settings", json={"apiKey": replacement})).status_code == 200
        assert store.value == replacement

        assert (await client.delete("/api/v1/ai/key")).status_code == 204
        assert (await client.delete("/api/v1/ai/key")).status_code == 204
        assert (await client.get("/api/v1/ai/settings")).json()["hasKey"] is False


@pytest.mark.parametrize("body", [{"apiKey": "  "}, {"apiKey": "short"}, {"apiKey": "x" * 4097}, {"apiKey": "sk-or-v1-" + "a" * 40, "extra": "no"}])
async def test_invalid_or_unsupported_settings_are_rejected_without_store_write(body):
    async with api() as (client, store):
        response = await client.put("/api/v1/ai/settings", json=body)
        assert response.status_code == 422
        assert store.writes == 0


async def test_failed_key_replacement_preserves_existing_key_and_reports_safe_error():
    async with api() as (client, store):
        prior = "sk-or-v1-" + "a" * 40
        await client.put("/api/v1/ai/settings", json={"apiKey": prior})
        store.fail_write = True
        response = await client.put("/api/v1/ai/settings", json={"apiKey": "sk-or-v1-" + "b" * 40})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "CREDENTIAL_STORE_UNAVAILABLE"
        assert prior not in response.text
        assert store.value == prior


@pytest.mark.parametrize("headers", [
    {"origin": "http://localhost:3000"},
    {"host": "localhost:8000", "origin": "http://127.0.0.1:3000"},
])
async def test_loopback_origin_aliases_allow_credential_mutation(headers):
    secret = "sk-or-v1-" + "e" * 40
    async with api() as (client, store):
        response = await client.put(
            "/api/v1/ai/settings",
            json={"apiKey": secret},
            headers=headers,
        )
        assert response.status_code == 200
        assert store.value == secret
        assert store.writes == 1


@pytest.mark.parametrize("headers", [
    {"origin": "https://attacker.invalid"},
    {"host": "attacker.invalid", "origin": "http://127.0.0.1"},
    {"origin": "http://attacker.invalid"},
    {"origin": "http://localhost", "sec-fetch-site": "cross-site"},
])
async def test_hostile_request_context_is_rejected_before_store_mutation(headers):
    async with api() as (client, store):
        response = await client.put(
            "/api/v1/ai/settings",
            json={"apiKey": "sk-or-v1-" + "c" * 40},
            headers=headers,
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "LOCAL_REQUEST_FORBIDDEN"
        assert store.writes == 0


async def test_absent_secure_store_reports_unavailable_without_fallback():
    class UnavailableCredentials(MemoryCredentials):
        @property
        def available(self):
            return False

        def get(self):
            raise RuntimeError("locked")

    async with api(UnavailableCredentials()) as (client, store):
        assert (await client.get("/api/v1/ai/settings")).json() == {
            "hasKey": False,
            "selectedModelId": None,
            "storeStatus": "unavailable",
        }
        response = await client.put("/api/v1/ai/settings", json={"apiKey": "sk-or-v1-" + "d" * 40})
        assert response.status_code == 503
        assert store.writes == 0


async def test_hostile_context_is_rejected_before_payload_validation():
    async with api() as (client, store):
        response = await client.put(
            "/api/v1/ai/settings",
            json={"unexpected": "request"},
            headers={"origin": "https://attacker.invalid"},
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "LOCAL_REQUEST_FORBIDDEN"
        assert store.writes == 0


async def test_hostile_delete_is_rejected_before_store_access():
    async with api() as (client, store):
        response = await client.delete(
            "/api/v1/ai/key",
            headers={"origin": "https://attacker.invalid"},
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "LOCAL_REQUEST_FORBIDDEN"
        assert store.deletes == 0
        assert store.writes == 0
