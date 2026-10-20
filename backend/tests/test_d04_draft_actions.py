"""Owner-authorized D-04 edit/decline routes: exact versions and no send bypass."""
import pytest
from fastapi.testclient import TestClient
from payrollpilot.app import create_app
from payrollpilot import kinds
from .test_c05_routes import client, EXC  # reuse isolated fake-messaging fixture


def draft(c):
    r = c.post('/api/messages/draft', json={'exception_ids': [EXC]})
    r.raise_for_status()
    return r.json()


def approve(c, b):
    return c.post('/api/approvals', json={'kind': 'message_send', 'target_id': b['id'],
        'target_version': b['text_hash'], 'scope_text': 'Send only this reviewed text to the test recipient'})


def test_edit_invalidates_approval_and_requires_new_exact_hash(client):
    b = draft(client)
    old = approve(client, b).json()
    edited = client.post(f"/api/messages/{b['id']}/edit", json={'target_version': b['text_hash'], 'text': 'Which job was the shift on?'})
    assert edited.status_code == 200
    new = edited.json()
    assert new['text_hash'] != b['text_hash'] and new['approval_id'] is None and new['state'] == 'draft'
    assert 'actual_recipient' not in new
    assert client.app.state.pp.db.get_approval(old['id'])['state'] == 'invalidated'
    assert client.post(f"/api/messages/{b['id']}/send").status_code == 403
    assert approve(client, b).status_code == 409
    assert approve(client, new).status_code == 200
    sent = client.post(f"/api/messages/{b['id']}/send")
    assert sent.status_code == 200
    retried = client.post(f"/api/messages/{b['id']}/send")
    assert retried.status_code == 200 and retried.json()['duplicate'] is True
    assert retried.json()['provider_message_id'] == sent.json()['provider_message_id']
    assert sum(e['type'] == 'message.sent' for e in client.get('/api/events').json()) == 1
    # Earlier exact text remains in the append-only record history.
    rows = client.app.state.pp.db._conn.execute('SELECT COUNT(*) FROM records WHERE kind=? AND id=?', (kinds.MESSAGE_BATCH, b['id'])).fetchone()[0]
    assert rows >= 4


def test_stale_edits_and_declines_do_not_change_current_draft(client):
    b = draft(client)
    current = client.post(f"/api/messages/{b['id']}/edit", json={'target_version': b['text_hash'], 'text': 'Updated question'}).json()
    for action, extra in [('edit', {'text': 'Stale text'}), ('decline', {})]:
        assert client.post(f"/api/messages/{b['id']}/{action}", json={'target_version': b['text_hash'], **extra}).status_code == 409
    stored = client.app.state.pp.db.get_record(kinds.MESSAGE_BATCH, b['id'])
    assert stored['text_hash'] == current['text_hash'] and not stored.get('declined_at')


def test_decline_persists_and_cannot_be_approved_or_sent_after_restart(client):
    b = draft(client)
    old = approve(client, b).json()
    r = client.post(f"/api/messages/{b['id']}/decline", json={'target_version': b['text_hash']})
    assert r.status_code == 200 and r.json()['declined_at']
    assert client.app.state.pp.db.get_approval(old['id'])['state'] == 'invalidated'
    restarted = TestClient(create_app(client.app.state.pp.settings))
    assert approve(restarted, b).status_code == 409
    assert restarted.post(f"/api/messages/{b['id']}/send").status_code == 409
    assert restarted.post(f"/api/messages/{b['id']}/edit", json={'target_version': b['text_hash'], 'text': 'Cannot revive'}).status_code == 409
    detail = restarted.get(f'/api/exceptions/{EXC}').json()
    assert detail['messages']['outbound'][0]['declined_at']
    assert restarted.app.state.pp.db.send_state(b['id']) is None


@pytest.mark.parametrize('action', ['edit', 'decline'])
def test_sent_batch_cannot_be_changed(client, action):
    b = draft(client)
    approve(client, b).raise_for_status()
    client.post(f"/api/messages/{b['id']}/send").raise_for_status()
    assert client.post(f"/api/messages/{b['id']}/{action}", json={'target_version': b['text_hash'], 'text': 'No change'}).status_code == 409


def test_stop_blocks_edits_but_owner_can_still_decline(client):
    b = draft(client)
    client.post('/api/run/stop').raise_for_status()
    assert client.post(f"/api/messages/{b['id']}/edit", json={'target_version': b['text_hash'], 'text': 'No change'}).status_code == 409
    assert client.post(f"/api/messages/{b['id']}/decline", json={'target_version': b['text_hash']}).status_code == 200


@pytest.mark.parametrize('text', ['   ', 'x' * 10001])
def test_invalid_edit_text_rejected(client, text):
    b = draft(client)
    assert client.post(f"/api/messages/{b['id']}/edit", json={'target_version': b['text_hash'], 'text': text}).status_code == 422
