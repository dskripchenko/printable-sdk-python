"""Client for the Printable integration API (``/api/integration``).

Zero runtime dependencies (stdlib urllib). Server-side only: the secret
key must never reach untrusted environments.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from .signer import Signer

Transport = Callable[[str, str, dict[str, Any] | None], tuple[int, str]]


class PrintableError(RuntimeError):
    """API-level error: non-2xx response or ``success: false`` envelope."""

    def __init__(self, message: str, status: int, error_key: str | None = None,
                 payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.error_key = error_key
        self.payload = payload or {}


class PrintableClient:
    """HMAC-signed client (simple and strict canonical modes).

    >>> client = PrintableClient(
    ...     base_url="https://printable.example.com",
    ...     token="erp-main-...", secret_key="...", salt="...",
    ... )
    >>> doc = client.print_form_create({"template": "invoice", "variables": {...}})
    >>> doc["link"]
    """

    def __init__(self, base_url: str, token: str, secret_key: str, salt: str,
                 strict: bool = False, timeout: int = 30,
                 transport: Transport | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._secret_key = secret_key
        self._strict = strict
        self._timeout = timeout
        self._signer = Signer(salt)
        self._transport = transport or self._urllib_transport

    # -- Templates ------------------------------------------------------

    def template_list(self) -> dict[str, Any]:
        return self.call("GET", "template/list")

    def template_contract(self, template: str, version: str | None = None,
                          locale: str | None = None) -> dict[str, Any]:
        return self.call("GET", "template/contract", _clean({
            "template": template, "version": version, "locale": locale,
        }))

    def template_export(self, template: str, version: str | None = None) -> dict[str, Any]:
        return self.call("GET", "template/export", _clean({
            "template": template, "version": version,
        }))

    def template_import(self, package_b64: str, group_id: int,
                        **options: Any) -> dict[str, Any]:
        return self.call("POST", "template/import", {
            **options, "package_b64": package_b64, "group_id": group_id,
        })

    def template_import_docx(self, docx_b64: str, group_id: int,
                             name: str | None = None) -> dict[str, Any]:
        return self.call("POST", "template/import-docx", _clean({
            "docx_b64": docx_b64, "group_id": group_id, "name": name,
        }))

    def template_import_xlsx(self, xlsx_b64: str, group: int | str,
                             name: str | None = None) -> dict[str, Any]:
        """Import an Excel workbook (.xlsx) as a template draft.

        One section per non-empty sheet, printed at the sheet's own print
        scale. ``group`` is an existing group's id, or a path
        ("Реестры / Отчёты") the service creates when it is missing.
        """
        return self.call("POST", "template/import-xlsx", _clean({
            "xlsx_b64": xlsx_b64,
            "group_id": group if isinstance(group, int) else None,
            "group": group if isinstance(group, str) else None,
            "name": name,
        }))

    # -- Print forms ----------------------------------------------------

    def print_form_create(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.call("POST", "print-form/create", params)

    def print_form_get(self, uuid: str, format: str = "link") -> dict[str, Any]:
        return self.call("GET", "print-form/get", {"uuid": uuid, "format": format})

    def print_form_signature_request(self, uuid: str, certificate: str,
                                     slot: str | None = None) -> dict[str, Any]:
        """Ask for the digest an external signer signs.

        For a document in ``awaiting_signature``, with the signer's
        certificate (PEM, or DER in base64 as CryptoPro exports it). Sign the
        digest into a detached CMS and pass it to
        :meth:`print_form_signature_complete` before ``expires_at``. Without
        ``slot`` — the signature field the document waits for.
        """
        return self.call("POST", "print-form/signature-request", _clean({
            "uuid": uuid, "certificate": certificate, "slot": slot,
        }))

    def print_form_signature_complete(self, uuid: str, cms: str, slot: str | None = None,
                                      format: str = "link") -> dict[str, Any]:
        """Hand in the external signature: the detached CMS (base64 or PEM).

        The answer is the document — ``done`` when every signature is in,
        else still ``awaiting_signature`` for the next signer.
        """
        return self.call("POST", "print-form/signature-complete", _clean({
            "uuid": uuid, "cms": cms, "slot": slot, "format": format,
        }))

    def print_form_signature_invite(self, uuid: str, email: str | None = None,
                                    slot: str | None = None,
                                    name: str | None = None) -> dict[str, Any]:
        """Invite the document's recipient to sign it themselves.

        The service issues a personal link to a signing page (CryptoPro
        browser plug-in, a detached .sig upload, or a PDF signed in its
        field). With ``email`` the service also sends the link by email.
        Without ``slot`` — the signature field the document waits for.
        Returns ``uuid``, ``slot``, ``sign_url``, ``expires_at``, ``sent``.
        """
        return self.call("POST", "print-form/signature-invite", _clean({
            "uuid": uuid, "slot": slot, "email": email, "name": name,
        }))

    def print_form_rules(self, template: str, version: str | None = None) -> dict[str, Any]:
        return self.call("GET", "print-form/rules", _clean({
            "template": template, "version": version,
        }))

    def print_form_batch(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.call("POST", "print-form/batch", params)

    def print_form_batch_get(self, uuid: str) -> dict[str, Any]:
        return self.call("GET", "print-form/batch-get", {"uuid": uuid})

    # -- Document drafts ------------------------------------------------

    def document_draft_create(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.call("POST", "document-draft/create", params)

    def document_draft_get(self, uuid: str) -> dict[str, Any]:
        return self.call("GET", "document-draft/get", {"uuid": uuid})

    # -- Webhooks -------------------------------------------------------

    def verify_webhook(self, raw_body: str, signature_header: str,
                       timestamp_header: str | int) -> bool:
        signature = signature_header
        if signature.startswith("sha256="):
            signature = signature[len("sha256="):]
        return self._signer.verify_webhook(
            signature, int(timestamp_header), raw_body, self._secret_key,
        )

    # -- Core -----------------------------------------------------------

    def call(self, method: str, endpoint: str,
             params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Signed call to any ``{controller}/{action}``; returns envelope payload."""
        timestamp = int(time.time())
        payload: dict[str, Any] = {**(params or {}), "timestamp": timestamp}

        if self._strict:
            hash_value = self._signer.sign_payload(payload, self._secret_key)
        else:
            hash_value = self._signer.sign_token(self._token, timestamp, self._secret_key)

        body: dict[str, Any] = {**payload, "token": self._token, "hash": hash_value}
        url = f"{self._base_url}/api/integration/{endpoint.lstrip('/')}"

        if method.upper() == "GET":
            url += "?" + urllib.parse.urlencode(
                {k: str(v) for k, v in body.items()}
            )
            status, raw = self._transport("GET", url, None)
        else:
            status, raw = self._transport(method.upper(), url, body)

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PrintableError(
                f"Printable API returned a non-JSON response (HTTP {status})", status,
            ) from exc

        payload_out = decoded.get("payload") or {}
        if status >= 400 or decoded.get("success") is not True:
            message = payload_out.get("message") or f"Printable API error (HTTP {status})"
            raise PrintableError(message, status, payload_out.get("errorKey"), payload_out)
        return payload_out

    def _urllib_transport(self, method: str, url: str,
                          body: dict[str, Any] | None) -> tuple[int, str]:
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode()
        request = urllib.request.Request(
            url, data=data, method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                return response.status, response.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()
        except urllib.error.URLError as exc:
            raise PrintableError(f"Printable API request failed: {exc.reason}", 0) from exc


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}
