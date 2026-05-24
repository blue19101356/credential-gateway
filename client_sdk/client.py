"""Credential Gateway client SDK."""

import os
import sys
import json
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from src.crypto.ecc_manager import (
    load_private_key,
    load_public_key,
    serialize_public_key,
    sign,
)
from src.crypto.hashing import sha256
from src.crypto.encryption import (
    decrypt_string,
    load_x25519_private_key,
    load_x25519_public_key,
    serialize_x25519_public_key,
)


class CredentialClient:
    def __init__(
        self,
        base_url: str,
        signing_private_key_pem: str,
        encryption_private_key_pem: str,
        app_id: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.signing_key = load_private_key(signing_private_key_pem)
        self.encryption_key = load_x25519_private_key(encryption_private_key_pem)
        self.app_id = app_id
        self._client = httpx.Client(timeout=30)

    # --- Registration ---

    @classmethod
    def register(
        cls,
        base_url: str,
        name: str,
        signing_private_key_pem: str,
        signing_public_key_pem: str,
        encryption_private_key_pem: str,
        encryption_public_key_pem: str,
    ) -> "CredentialClient":
        client = cls.__new__(cls)
        client.base_url = base_url.rstrip("/")
        client.signing_key = load_private_key(signing_private_key_pem)
        client.encryption_key = load_x25519_private_key(encryption_private_key_pem)
        client._client = httpx.Client(timeout=30)

        resp = client._client.post(
            f"{client.base_url}/v1/applications",
            json={
                "name": name,
                "ed25519_public_key": signing_public_key_pem.strip(),
                "x25519_public_key": encryption_public_key_pem.strip(),
            },
        )
        resp.raise_for_status()
        data = resp.json()
        client.app_id = data["id"]
        return client

    # --- Credential operations ---

    def store_credential(self, type_: str, name: str, value: str, tags: str | None = None) -> dict:
        body = {"type": type_, "name": name, "value": value}
        if tags:
            body["tags"] = tags
        return self._signed_request("POST", "/v1/credentials", body)

    def retrieve_credential(self, credential_id: str) -> str:
        data = self._signed_request("GET", f"/v1/credentials/{credential_id}")
        encrypted = data["encrypted_data"]
        return decrypt_string(encrypted, self.encryption_key)

    def list_credentials(self, type_: str | None = None) -> list[dict]:
        path = "/v1/credentials"
        if type_:
            path += f"?type={type_}"
        return self._signed_request("GET", path)

    def delete_credential(self, credential_id: str) -> None:
        self._signed_request("DELETE", f"/v1/credentials/{credential_id}")

    # --- Internal ---

    def _signed_request(self, method: str, path: str, body: dict | None = None) -> Any:
        body_bytes = b""
        if body is not None:
            body_bytes = json.dumps(body).encode("utf-8")

        digest = sha256(body_bytes)
        signature = sign(self.signing_key, digest)

        headers = {
            "Content-Type": "application/json",
            "X-App-Id": self.app_id,
            "X-Signature": signature.hex(),
        }

        url = f"{self.base_url}{path}"
        if body is not None:
            resp = self._client.request(method, url, headers=headers, content=body_bytes)
        else:
            resp = self._client.request(method, url, headers=headers)

        resp.raise_for_status()

        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def close(self):
        self._client.close()
