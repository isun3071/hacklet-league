"""Detection-primitive unit tests. Focus: precision of the content matchers — they must catch real
problems and must NOT flag benign content (a false positive wrongly penalizes).
"""
from hacklet_runner.probes import (
    response_is_dotenv,
    response_is_git_config,
    response_is_git_head,
    response_leaks_secret,
)


class _Resp:
    def __init__(self, text: str, status: int = 200):
        self.text = text
        self.status_code = status


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


def test_detects_exposed_files():
    assert response_is_dotenv(_Resp("DATABASE_URL=postgres://x\nSECRET_KEY=abc"))
    assert response_is_dotenv(_Resp("export GITHUB_TOKEN=ghp_xyz\n"))   # export prefix + TOKEN key
    assert response_is_dotenv(_Resp("  STRIPE_KEY=sk_live_xyz\n"))      # indented + bare *_KEY
    assert response_is_git_config(_Resp("[core]\n\trepositoryformatversion = 0\n"))
    assert response_is_git_head(_Resp("ref: refs/heads/main\n"))        # symbolic ref
    assert response_is_git_head(_Resp("a" * 40 + "\n"))                 # detached HEAD (raw SHA)


def test_exposure_needs_200_and_signature():
    assert not response_is_dotenv(_Resp("DATABASE_URL=x", status=404))   # not actually served
    assert not response_is_dotenv(_Resp("<html><body>hi</body></html>"))  # 200 but not a .env
    assert not response_is_git_head(_Resp("<html>not found</html>"))     # 200, wrong content
