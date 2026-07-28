# Printable SDK for Python

Official Python client for the Printable document-generation service
integration API: templates, print-forms, batch rendering, document drafts
and webhook verification — with HMAC request signing (simple and strict
canonical modes) built in and byte-compatible with the server implementation.

Zero runtime dependencies (stdlib only). Python 3.10+. **Server-side
only** — the secret key must never reach untrusted environments.

## Install

```bash
pip install printable-sdk
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
`template_import` · `template_import_docx` · `print_form_create` ·
`print_form_get` · `print_form_rules` · `print_form_batch` ·
`print_form_batch_get` · `document_draft_create` · `document_draft_get` ·
`call(method, endpoint, params)` (escape hatch).

Every method returns the decoded `payload` dict of the response envelope.
Errors (non-2xx or `success: false`) raise `PrintableError` with
`.status`, `.error_key` and the raw error `.payload`.

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
