"""Detection-primitive unit tests. Focus: the secrets matcher's precision — it must catch real
server secrets and must NOT flag public-by-design values (a false positive wrongly penalizes).
"""
from hacklet_runner.probes import response_leaks_secret


class _Resp:
    def __init__(self, text: str):
        self.text = text


def test_detects_real_secrets():
    assert response_leaks_secret(_Resp("AKIAIOSFODNN7EXAMPLE"))                 # AWS key id
    assert response_leaks_secret(_Resp('k="sk_live_abcdef0123456789ABCDEF"'))   # Stripe live secret
    assert response_leaks_secret(_Resp("ghp_" + "a" * 36))                      # GitHub PAT
    assert response_leaks_secret(_Resp("-----BEGIN PRIVATE KEY-----\nMIIE..."))  # private key block


def test_ignores_public_by_design():
    # Firebase web apiKey, Stripe publishable key, and plain JS are NOT secrets.
    assert not response_leaks_secret(_Resp('apiKey: "AIzaSyD-EXAMPLE_firebase_public_key_x12345"'))
    assert not response_leaks_secret(_Resp("pk_live_publishablekey1234567890"))
    assert not response_leaks_secret(_Resp('const config = { api: "/api" };'))
