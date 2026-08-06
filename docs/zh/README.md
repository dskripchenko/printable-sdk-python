# Printable SDK for Python

面向文档生成服务 [Printable](https://printable.dev-cloud.space) 集成 API 的官方 Python 客户端：
模板、打印表单、批量渲染、文档草稿以及 webhook 校验。HMAC 请求签名
（简单模式与严格规范模式）已内置，并与服务端实现逐字节一致。

> 🌐 [English](../../README.md) · [Deutsch](../de/README.md) · [Русский](../ru/README.md) · **中文**

运行时零依赖（仅标准库）。Python 3.10+。**仅限服务端**——密钥绝不能进入不可信环境。

## 安装

```bash
pip install printable-api-sdk
```

## 快速开始

```python
from printable_sdk import PrintableClient

client = PrintableClient(
    base_url="https://printable.example.com",
    token="erp-main-7f3a",
    secret_key=os.environ["PRINTABLE_SECRET"],
    salt=os.environ["PRINTABLE_SALT"],
    strict=False,  # 若该凭据开启了“校验完整载荷哈希”，则填 True
)

# 渲染一份文档
doc = client.print_form_create({
    "template": "invoice",
    "variables": {"company": {"name": "ACME Ltd"}},
    "format": "link",
})
print(doc["link"])

# 批量生成，打包并邮件送达
batch = client.print_form_batch({
    "template": "certificate",
    "items": [{"variables": {"name": "Alice"}}, {"variables": {"name": "Bob"}}],
    "archive": True,
    "deliver": {"email": "hr@example.com"},
})
status = client.print_form_batch_get(batch["uuid"])
```

## API 一览

`template_list` · `template_contract` · `template_export` ·
`template_import` · `template_import_docx` · `print_form_create` ·
`print_form_get` · `print_form_rules` · `print_form_batch` ·
`print_form_batch_get` · `document_draft_create` · `document_draft_get` ·
`call(method, endpoint, params)`

每个方法都返回响应信封中解码后的 `payload` 字典。
出错时（非 2xx 或 `success: false`）抛出 `PrintableError`，其中带有
`.status`、`.error_key` 以及原始的错误 `.payload`。

## Webhook

```python
valid = client.verify_webhook(
    raw_body,  # raw request body string
    request.headers["X-Printable-Signature"],
    request.headers["X-Printable-Timestamp"],
)
```

## 为集成打桩测试

注入自定义的 `transport` 即可为 HTTP 打桩：

```python
client = PrintableClient(
    ...,
    transport=lambda method, url, body: (200, '{"success":true,"payload":{"ok":true}}'),
)
```

## 许可证

MIT
