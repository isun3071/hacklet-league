"""The two email predicates (probes.email_never_arrives / email_verification_inert) map the shared
EmailVerifyResult onto a probe verdict. The flow itself is tested in test_email_verify; here we monkeypatch it
to canned results and check the mapping + the report_only + N/A guards, so no network or registration runs."""
import types

from sloptic import probes
from sloptic.email_verify import EmailMessage, EmailVerifyResult, MockReceiver

RX = MockReceiver()   # a non-None receiver; _run_email_flow is monkeypatched, so it is never actually used


def _ctx(email=None, headers=None):
    return types.SimpleNamespace(email=email, headers=headers, base_url="http://app.test",
                                 profile=None, _email_cache={}, evidence={})


def _canned(monkeypatch, res):
    monkeypatch.setattr(probes, "_run_email_flow", lambda ctx: res)


def test_na_without_a_receiver():
    c = _ctx(email=None)
    assert probes.email_never_arrives(c, None) is None
    assert "no email receiver" in c.evidence["na_reason"]
    assert c.evidence["report_only"] is True     # always off-score in v1


def test_na_with_a_provided_session():
    c = _ctx(email=RX, headers={"Cookie": "session=x"})
    assert probes.email_never_arrives(c, None) is None
    assert "session was supplied" in c.evidence["na_reason"]


def test_na_when_signup_is_not_email_gated(monkeypatch):
    _canned(monkeypatch, EmailVerifyResult(attempted=True, email_gated=False, na_reason="not gated"))
    assert probes.email_never_arrives(_ctx(email=RX), None) is None
    assert probes.email_verification_inert(_ctx(email=RX), None) is None


def test_email_001_fires_when_gated_and_no_email(monkeypatch):
    _canned(monkeypatch, EmailVerifyResult(attempted=True, email_gated=True, email_arrived=False, detail="no mail"))
    c = _ctx(email=RX)
    assert probes.email_never_arrives(c, None) is True
    assert c.evidence["report_only"] is True and c.evidence["email_gated"] is True
    # 002 cannot judge a link that never arrived -> N/A, never a false fire
    assert probes.email_verification_inert(_ctx(email=RX), None) is None


def test_email_002_fires_when_link_establishes_no_session(monkeypatch):
    msg = EmailMessage.parse("hl@app.test", "Verify", "http://app.test/v")
    _canned(monkeypatch, EmailVerifyResult(attempted=True, email_gated=True, email_arrived=True,
                                           acted_on_verification=True, session_after_verify=False, message=msg))
    assert probes.email_verification_inert(_ctx(email=RX), None) is True
    assert probes.email_never_arrives(_ctx(email=RX), None) is False   # 001 clean: the email DID arrive


def test_both_clean_when_the_whole_flow_works(monkeypatch):
    msg = EmailMessage.parse("hl@app.test", "Verify", "http://app.test/v")
    _canned(monkeypatch, EmailVerifyResult(attempted=True, email_gated=True, email_arrived=True,
                                           acted_on_verification=True, session_after_verify=True, message=msg))
    assert probes.email_never_arrives(_ctx(email=RX), None) is False
    assert probes.email_verification_inert(_ctx(email=RX), None) is False


def test_email_002_na_on_a_code_only_email(monkeypatch):
    msg = EmailMessage.parse("hl@app.test", "Code", "your verification code is 903217")
    _canned(monkeypatch, EmailVerifyResult(attempted=True, email_gated=True, email_arrived=True,
                                           acted_on_verification=False, message=msg,
                                           detail="no followable verification link"))
    c = _ctx(email=RX)
    assert probes.email_verification_inert(c, None) is None   # could not act -> N/A, never a fire
    assert "followable" in c.evidence["na_reason"]
