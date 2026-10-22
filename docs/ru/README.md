# Printable SDK для Python

Официальный клиент на Python к интеграционному API сервиса генерации документов
[Printable](https://printable.dev-cloud.space): шаблоны, печатные формы, пакетная
печать, черновики документов и проверка вебхуков. Подпись запросов HMAC
(простой и строгий канонический режимы) встроена и побайтово совпадает с
серверной реализацией.

> 🌐 [English](../../README.md) · [Deutsch](../de/README.md) · **Русский** · [中文](../zh/README.md)

Никаких зависимостей в рантайме (только стандартная библиотека). Python 3.10+.
**Только на сервере** — секретный ключ не должен попадать в недоверенное окружение.

## Установка

```bash
pip install printable-api-sdk
```

## Быстрый старт

```python
from printable_sdk import PrintableClient

client = PrintableClient(
    base_url="https://printable.example.com",
    token="erp-main-7f3a",
    secret_key=os.environ["PRINTABLE_SECRET"],
    salt=os.environ["PRINTABLE_SALT"],
    strict=False,  # True, если у ключа включена «проверка хеша всего тела»
)

# Печать документа
doc = client.print_form_create({
    "template": "invoice",
    "variables": {"company": {"name": "ACME Ltd"}},
    "format": "link",
})
print(doc["link"])

# Пакет с архивом и отправкой на почту
batch = client.print_form_batch({
    "template": "certificate",
    "items": [{"variables": {"name": "Alice"}}, {"variables": {"name": "Bob"}}],
    "archive": True,
    "deliver": {"email": "hr@example.com"},
})
status = client.print_form_batch_get(batch["uuid"])
```

## Поверхность API

`template_list` · `template_contract` · `template_export` ·
`template_import` · `template_import_docx` · `template_import_xlsx` ·
`print_form_create` ·
`print_form_get` · `print_form_rules` · `print_form_signature_request` ·
`print_form_signature_complete` · `print_form_signature_invite` ·
`print_form_batch` ·
`print_form_batch_get` · `document_draft_create` · `document_draft_get` ·
`call(method, endpoint, params)`

Каждый метод возвращает раскодированный словарь `payload` из конверта ответа.
Ошибки (не-2xx или `success: false`) поднимают `PrintableError` с полями
`.status`, `.error_key` и исходным `.payload` ошибки.

## Подпись и защита

`print-form/create` и `print-form/batch` принимают необязательные параметры — они передаются в params как есть:

- `preset` — код пресета печати вместо `template` (его принимает и `document-draft/create`);
- `signing` — профиль подписи для каждого поля, видимая или невидимая подпись, основание и `recipients` — контрагенты, которые подписывают документ сами;
- `protection` — защита PDF: `{"generate": true}` — пароль сгенерирует сервис, либо свой пароль в поле `password`; необязательное `permissions` — `read_print`, `read_only` или `forms_sign`.

В ответе тогда есть блок `protection` (`protected`, `permissions`, `password`, `owner_password`). **Пароли приходят только один раз** — в ответе, который выпускает документ; дальше они замаскированы (`••••••••`), так что сохраните их сразу. У каждого элемента `signature.slots[]` могут быть `method` (`cms`, `plugin`, `pdf` или `sig`) и `signature_link` — отделённая `.sig` получателя.

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
# Пароль приходит только в этом ответе — сохраните его сейчас
protection = doc["protection"]

# Передайте ссылку сами или дайте сервису отправить её письмом
invite = client.print_form_signature_invite(doc["uuid"], "buyer@example.com", "buyer", "Buyer LLC")
print(invite["sign_url"])
```

`print_form_signature_invite()` приглашает получателя подписать документ: возвращает `sign_url` — персональную ссылку на страницу подписи (плагин КриптоПро в браузере, загрузка отделённой `.sig` или PDF, подписанный в своём поле) — и `expires_at`. С адресом почты сервис ещё и отправит ссылку письмом (`sent`).

## Вебхуки

```python
valid = client.verify_webhook(
    raw_body,  # raw request body string
    request.headers["X-Printable-Signature"],
    request.headers["X-Printable-Timestamp"],
)
```

## Проверка интеграции

Подставьте свой `transport`, чтобы заглушить HTTP:

```python
client = PrintableClient(
    ...,
    transport=lambda method, url, body: (200, '{"success":true,"payload":{"ok":true}}'),
)
```

## Лицензия

MIT
