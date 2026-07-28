import json
import urllib.parse

import pytest

from printable_sdk import PrintableClient, PrintableError, Signer


def make_client(strict=False, status=200, response='{"success":true,"payload":{"ok":1}}'):
    captured = []

    def transport(method, url, body):
        captured.append({"method": method, "url": url, "body": body})
        return status, response

    client = PrintableClient(
        base_url="https://printable.test",
        token="tok-1", secret_key="sec-1", salt="salt-123",
        strict=strict, transport=transport,
    )
    return client, captured


def test_post_sends_signed_body_with_simple_hash():
    client, captured = make_client()
    payload = client.print_form_create({"template": "invoice", "variables": {"a": 1}})

    assert payload == {"ok": 1}
    request = captured[0]
    assert request["method"] == "POST"
    assert request["url"] == "https://printable.test/api/integration/print-form/create"
    body = request["body"]
    assert body["token"] == "tok-1"
    assert body["hash"] == Signer("salt-123").sign_token("tok-1", body["timestamp"], "sec-1")


def test_strict_mode_signs_payload_without_token_and_hash():
    client, captured = make_client(strict=True)
    client.print_form_create({"template": "invoice"})

    body = dict(captured[0]["body"])
    hash_value = body.pop("hash")
    body.pop("token")
    assert hash_value == Signer("salt-123").sign_payload(body, "sec-1")


def test_get_puts_auth_into_query_string():
    client, captured = make_client()
    client.print_form_get("0f8fad5b-d9cb-469f-a165-70867728950e")

    request = captured[0]
    assert request["method"] == "GET"
    assert request["body"] is None
    query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(request["url"]).query))
    assert query["uuid"] == "0f8fad5b-d9cb-469f-a165-70867728950e"
    assert query["token"] == "tok-1"
    assert "timestamp" in query and "hash" in query


def test_error_envelope_raises_with_error_key():
    client, _ = make_client(
        status=401,
        response='{"success":false,"payload":{"errorKey":"auth-token-invalid","message":"Bad token"}}',
    )
    with pytest.raises(PrintableError) as exc:
        client.template_list()
    assert exc.value.status == 401
    assert exc.value.error_key == "auth-token-invalid"
    assert str(exc.value) == "Bad token"


def test_non_json_response_raises():
    client, _ = make_client(status=502, response="<html>Bad gateway</html>")
    with pytest.raises(PrintableError, match="non-JSON"):
        client.template_list()


def test_verify_webhook_accepts_prefixed_header():
    client, _ = make_client()
    import hashlib
    import hmac
    signature = "sha256=" + hmac.new(
        b"sec-1", b'1753600000.{"uuid":"abc"}', hashlib.sha256
    ).hexdigest()
    assert client.verify_webhook('{"uuid":"abc"}', signature, "1753600000")
    assert not client.verify_webhook('{"uuid":"abc"}', "sha256=deadbeef", "1753600000")
