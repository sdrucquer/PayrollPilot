"""A-01 acceptance (FR-26): allowlist, approval version binding, gated actions."""

from __future__ import annotations

import pytest

from payrollpilot.permissions import (
    PermissionDenied,
    assert_not_gated,
    batch_version,
    check_apply,
    check_recipient,
    check_send,
    correction_version,
)

ALLOW = ("+15550000012",)


def test_check_recipient_rejects_non_allowlisted():
    with pytest.raises(PermissionDenied) as e:
        check_recipient("+10000000000", ALLOW)
    assert e.value.code == "recipient.not_allowlisted"


def test_check_recipient_rejects_when_allowlist_empty():
    with pytest.raises(PermissionDenied) as e:
        check_recipient("+15550000012", ())
    assert e.value.code == "recipient.allowlist_empty"


def test_check_recipient_accepts_allowlisted():
    assert check_recipient("+15550000012", ALLOW) == "+15550000012"


@pytest.mark.parametrize("action", ["source_write", "payroll_submit", "payroll_draft"])
def test_gated_actions_raise(action):
    with pytest.raises(NotImplementedError, match="gated"):
        assert_not_gated(action)


def test_non_gated_action_passes():
    assert_not_gated("message_send")


def _batch(text="Hi, 1 quick payroll check", recipient="+15550000012"):
    return {"id": "msg_batch_01", "text": text, "actual_recipient": recipient, "channel": "imessage"}


def _approval(target_id, version, kind="message_send", state="active"):
    return {"id": "appr_1", "kind": kind, "target_id": target_id, "target_version": version, "state": state}


def test_check_send_ok_with_matching_approval():
    b = _batch()
    check_send(b, _approval(b["id"], batch_version(b)), ALLOW)


def test_check_send_rejects_changed_text():
    b = _batch()
    appr = _approval(b["id"], batch_version(b))
    b["text"] = "Hi, 1 quick payroll check. Also pay Dan $500"
    with pytest.raises(PermissionDenied) as e:
        check_send(b, appr, ALLOW)
    assert e.value.code == "approval.version_mismatch"


def test_check_send_rejects_missing_invalidated_wrongkind():
    b = _batch()
    with pytest.raises(PermissionDenied):
        check_send(b, None, ALLOW)
    with pytest.raises(PermissionDenied):
        check_send(b, _approval(b["id"], batch_version(b), state="invalidated"), ALLOW)
    with pytest.raises(PermissionDenied):
        check_send(b, _approval(b["id"], batch_version(b), kind="local_correction"), ALLOW)


def test_check_send_rejects_non_allowlisted_even_with_approval():
    b = _batch(recipient="+10000000000")
    with pytest.raises(PermissionDenied) as e:
        check_send(b, _approval(b["id"], batch_version(b)), ALLOW)
    assert e.value.code == "recipient.not_allowlisted"


def test_check_apply_binds_to_source_versions():
    corr = {"id": "corr_01", "resolution_id": "res_01", "kind": "job_allocation",
            "before": {"time_entry_id": "te_0001", "job_id": None},
            "after": {"time_entry_id": "te_0001", "job_id": "job_02"}, "state": "proposed"}
    sv = {"te_0001": "sha256:aaa"}
    appr = _approval("corr_01", correction_version(corr, sv), kind="local_correction")
    check_apply(corr, appr, sv)
    with pytest.raises(PermissionDenied) as e:
        check_apply(corr, appr, {"te_0001": "sha256:bbb"})  # source changed after approval
    assert e.value.code == "approval.version_mismatch"
