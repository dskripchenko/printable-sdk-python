# Printable-SDK für Python

Offizieller Python-Client für die Integrations-API des Dokumentendienstes
[Printable](https://printable.dev-cloud.space): Vorlagen, Druckformulare,
Stapelverarbeitung, Dokumententwürfe und Webhook-Prüfung. Die HMAC-Signatur der
Anfragen (einfacher und strenger kanonischer Modus) ist eingebaut und
byteweise identisch mit der Server-Implementierung.

> 🌐 [English](../../README.md) · **Deutsch** · [Русский](../ru/README.md) · [中文](../zh/README.md)

Keine Laufzeitabhängigkeiten (nur die Standardbibliothek). Python 3.10+.
**Nur serverseitig** — der geheime Schlüssel darf nie in eine nicht
vertrauenswürdige Umgebung gelangen.

## Installation

```bash
pip install printable-api-sdk
```

## Schnellstart

```python
from printable_sdk import PrintableClient

client = PrintableClient(
    base_url="https://printable.example.com",
    token="erp-main-7f3a",
    secret_key=os.environ["PRINTABLE_SECRET"],
    salt=os.environ["PRINTABLE_SALT"],
    strict=False,  # True, wenn für den Zugang „gesamten Payload-Hash prüfen“ aktiv ist
)

# Ein Dokument rendern
doc = client.print_form_create({
    "template": "invoice",
    "variables": {"company": {"name": "ACME Ltd"}},
    "format": "link",
})
print(doc["link"])

# Stapel mit Archiv und E-Mail-Versand
batch = client.print_form_batch({
    "template": "certificate",
    "items": [{"variables": {"name": "Alice"}}, {"variables": {"name": "Bob"}}],
    "archive": True,
    "deliver": {"email": "hr@example.com"},
})
status = client.print_form_batch_get(batch["uuid"])
```

## API-Oberfläche

`template_list` · `template_contract` · `template_export` ·
`template_import` · `template_import_docx` · `print_form_create` ·
`print_form_get` · `print_form_rules` · `print_form_batch` ·
`print_form_batch_get` · `document_draft_create` · `document_draft_get` ·
`call(method, endpoint, params)`

Jede Methode gibt das dekodierte `payload`-Dict aus dem Antwort-Umschlag zurück.
Fehler (nicht-2xx oder `success: false`) lösen `PrintableError` aus — mit
`.status`, `.error_key` und dem rohen Fehler-`.payload`.

## Webhooks

```python
valid = client.verify_webhook(
    raw_body,  # raw request body string
    request.headers["X-Printable-Signature"],
    request.headers["X-Printable-Timestamp"],
)
```

## Integration testen

Injizieren Sie einen eigenen `transport`, um HTTP zu stubben:

```python
client = PrintableClient(
    ...,
    transport=lambda method, url, body: (200, '{"success":true,"payload":{"ok":true}}'),
)
```

## Lizenz

MIT
