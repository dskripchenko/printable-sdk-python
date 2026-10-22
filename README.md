# Printable SDK for Python

Official Python client for the Printable document-generation service
integration API: templates, print-forms, batch rendering, document drafts
and webhook verification — with HMAC request signing (simple and strict
canonical modes) built in and byte-compatible with the server implementation.

> 🌐 **English** · [Deutsch](docs/de/README.md) · [Русский](docs/ru/README.md) · [中文](docs/zh/README.md)

Zero runtime dependencies (stdlib only). Python 3.10+. **Server-side
only** — the secret key must never reach untrusted environments.

## Install

```bash
pip install printable-api-sdk
```

## Quick start

```python
from printable_sdk import PrintableClient

client = PrintableClient(
    base_url="https://printable.example.com",
    token="erp-main-7f3a",
    secret_key=os.environ["PRINTABLE_SECRET"],
    salt=os.environ["PRINTABLE_SALT"],
    strict=False,  # True if the credential has "verify full payload hash" enabled
)

# Render a document
doc = client.print_form_create({
    "template": "invoice",
    "variables": {"company": {"name": "ACME Ltd"}},
    "format": "link",
})
print(doc["link"])

# Batch with archive + email delivery
batch = client.print_form_batch({
    "template": "certificate",
    "items": [{"variables": {"name": "Alice"}}, {"variables": {"name": "Bob"}}],
    "archive": True,
    "deliver": {"email": "hr@example.com"},
})
status = client.print_form_batch_get(batch["uuid"])
```

## API surface

`template_list` · `template_contract` · `template_export` ·
`template_import` · `template_import_docx` · `template_import_xlsx` ·
`print_form_create` ·
`print_form_get` · `print_form_rules` · `print_form_signature_request` ·
`print_form_signature_complete` · `print_form_signature_invite` ·
`print_form_batch` ·
`print_form_batch_get` · `document_draft_create` · `document_draft_get` ·
`call(method, endpoint, params)` (escape hatch).

Every method returns the decoded `payload` dict of the response envelope.
Errors (non-2xx or `success: false`) raise `PrintableError` with
`.status`, `.error_key` and the raw error `.payload`.

## Signing and protection

`print-form/create` and `print-form/batch` accept optional parameters, passed as-is in the params:

- `preset` — a print-preset code used instead of `template` (`document-draft/create` accepts it too);
- `signing` — a signature profile per slot, a visible or invisible signature, the reason, and `recipients` — the counterparties who sign the document themselves;
- `protection` — PDF protection: `{"generate": true}` lets the service generate the password, or pass your own one under `password`; the optional `permissions` is `read_print`, `read_only` or `forms_sign`.

The response then carries a `protection` block (`protected`, `permissions`, `password`, `owner_password`). **Passwords are returned only once** — in the response that issues the document; afterwards they come back masked (`••••••••`), so store them right away. Each `signature.slots[]` item may carry `method` (`cms`, `plugin`, `pdf` or `sig`) and `signature_link` — the recipient's detached `.sig`.

```python
doc = client.print_form_create({
    "preset": "contract-signed",
    "variables": {"contract": {"number": 15}},
    "signing": {
        "slots": {"company": {"profile": "ceo"}},
        "invisible": False,
        "reason": "Contract 15",
        "recipients": {"buyer": {"email": "buyer@example.com", "name": "Buyer LLC"}},
    },
    "protection": {"generate": True, "permissions": "read_print"},
})
# The password comes only in this response — store it now
protection = doc["protection"]

# Hand the link over yourself, or let the service email it
invite = client.print_form_signature_invite(doc["uuid"], "buyer@example.com", "buyer", "Buyer LLC")
print(invite["sign_url"])
```

`print_form_signature_invite()` invites the recipient to sign: it returns `sign_url` — a personal link to the signing page (CryptoPro browser plug-in, a detached `.sig` upload, or a PDF signed in its field) — and `expires_at`. With an email address the service also sends the link (`sent`).

## Webhooks

```python
valid = client.verify_webhook(
    raw_body,  # raw request body string
    request.headers["X-Printable-Signature"],
    request.headers["X-Printable-Timestamp"],
)
```

## Testing your integration

Inject a custom `transport` to stub HTTP:

```python
client = PrintableClient(
    ...,
    transport=lambda method, url, body: (200, '{"success":true,"payload":{"ok":true}}'),
)
```

## License

MIT
