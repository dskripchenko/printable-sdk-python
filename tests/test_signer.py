"""Vectors generated from the Printable server implementation
(App\\Auth\\HashSigner, salt-123 / sec-1) — byte-compatibility contract."""

import pytest

from printable_sdk import Signer, canonicalize

SALT = "salt-123"
SECRET = "sec-1"

VECTORS = [
    (
        "sorted keys + list preserved",
        {"b": 1, "a": "x", "nested": {"z": True, "a": [3, 1, 2]}},
        '{"a":"x","b":1,"nested":{"a":[3,1,2],"z":true}}',
        "f14fc443af8b3891f927aeb32c725923a4dc42fbf78eba2ce1439940be4ec5c2",
    ),
    (
        "unicode + numeric string",
        {"template": "invoice", "timestamp": 1753600000,
         "variables": {"user": {"name": "Иван/Ко", "age": "42"}}},
        '{"template":"invoice","timestamp":1753600000,"variables":{"user":{"age":42,"name":"Иван/Ко"}}}',
        "3ede97642552144bbb774d077f56bc9c5fc9fe16e8d529a1941d7d155dd3faa6",
    ),
    (
        "numeric-check edge cases",
        {"num_str": "100.0", "exp": "1e3", "zeros": "007", "plain": "text",
         "empty_obj": {}, "empty_arr": []},
        '{"empty_arr":[],"empty_obj":[],"exp":1000,"num_str":100,"plain":"text","zeros":7}',
        "35698b058d732971e4f74a3ef78db7ea1662b5758e03f353500dc2f9f7448be4",
    ),
    (
        "nested objects in list + null + false",
        {"list": {"b": 2, "items": [{"k": "v", "a": 1}, {"x": None}]}, "flag": False},
        '{"flag":false,"list":{"b":2,"items":[{"a":1,"k":"v"},{"x":null}]}}',
        "be151b065cdd8f2eb10d79a463ddc7467a185d154255fb427335574b8acbc845",
    ),
]


def test_sign_token_matches_server_simple_mode():
    signer = Signer(SALT)
    assert signer.sign_token("tok-1", 1753600000, SECRET) == (
        "bf9a3d9e15dbac35b13b0324bac385564bcec7a1d9f4fc56c7da5293da3ebf02"
    )


@pytest.mark.parametrize("name,payload,canonical,digest", VECTORS)
def test_canonicalize_and_sign_payload(name, payload, canonical, digest):
    assert canonicalize(payload) == canonical
    assert Signer(SALT).sign_payload(payload, SECRET) == digest


def test_sequential_key_objects_become_arrays():
    assert canonicalize({"list": {"0": "a", "1": "b"}}) == '{"list":["a","b"]}'


def test_verify_webhook_matches_server_signature():
    signer = Signer(SALT)
    assert signer.verify_webhook(
        "7641aadedab7b606585ba0c68ddfe4583b778b7a9bef62c700c76f9596dc9141",
        1753600000, '{"uuid":"abc"}', SECRET,
    )
    assert not signer.verify_webhook("deadbeef", 1753600000, '{"uuid":"abc"}', SECRET)


def test_rejects_empty_salt():
    with pytest.raises(ValueError):
        Signer("")
