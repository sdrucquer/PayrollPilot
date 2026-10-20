"""Essential Band deletion/failure tests. All Band doubles are explicitly labeled."""
import dataclasses

from fastapi.testclient import TestClient

from payrollpilot.app import create_app
from payrollpilot.band import BandError, NullBand, deliver_to_payroll
from .test_c05_routes import client, FakeBand, _with_band, _sent_batch, EXC


def draft(c):
    return c.post('/api/messages/draft', json={'exception_ids': [EXC]})


def approval(c,b):
    c.post('/api/approvals',json={'kind':'message_send','target_id':b['id'],'target_version':b['target_version'],'scope_text':'Send exact reviewed test question'}).raise_for_status()


def test_deleting_band_blocks_home_draft_without_effects(client):
    comms=_with_band(client);comms['band']=NullBand()
    before=client.app.state.pp.db.get_record('exception',EXC)
    r=draft(client)
    assert r.status_code==503 and r.json()['error']=='band_required'
    db=client.app.state.pp.db
    assert db.list_records('message_batch')==[]
    assert db.get_record('exception',EXC)==before
    assert client.app.state.pp.messaging.sent==[]


def test_home_direct_draft_requires_room_handoff_claim_and_persisted_proof(client):
    comms=_with_band(client);band=comms['band']
    b=draft(client).json()
    e=client.app.state.pp.db.get_record('exception',EXC)
    assert e['owner_agent']=='resolution' and e['state']=='investigating'
    assert e['band_handoff']['accepted'] and e['band_handoff']['task_uid']
    assert e['band_handoff']['room_id']==band.room_id
    assert '[handoff.requested]' in band.posts[0][1]
    assert '@sdrucquer/pp-resolution' in band.posts[0][1]
    assert any('[decision.requested]' in text for _,text in band.posts)
    assert b['band_coordination_required'] and b['band_decision_message_id']
    assert client.app.state.pp.messaging.sent==[]


def test_handoff_delivery_failure_never_creates_draft(client,monkeypatch):
    import importlib
    orchestration=importlib.import_module("payrollpilot.band.handoff")
    _with_band(client)
    monkeypatch.setattr(orchestration,'_wait_for',lambda *a,**k:None)
    r=draft(client)
    assert r.status_code==504
    assert client.app.state.pp.db.list_records('message_batch')==[]
    assert client.app.state.pp.db.get_record('exception',EXC)['owner_agent']=='audit'


def test_owner_decision_publish_failure_is_not_ignored(client):
    class FailDecision(FakeBand):
        def post(self,agent,text):
            if '[decision.requested]' in text:raise BandError('Test Band unavailable for decision')
            return super().post(agent,text)
    comms=_with_band(client);comms['band']=FailDecision()
    r=draft(client)
    assert r.status_code==502
    assert client.app.state.pp.db.list_records('message_batch')==[]
    assert client.app.state.pp.messaging.sent==[]
    assert not any(e['type']=='message.drafted' for e in client.get('/api/events').json())


def test_disabled_or_unreachable_band_blocks_new_send_before_provider(client):
    comms=_with_band(client);b=draft(client).json();approval(client,b)
    comms['band']=NullBand()
    assert client.post(f"/api/messages/{b['id']}/send").status_code==503
    class Unreachable(FakeBand):
        def inbox(self,*a):raise BandError('Test daemon unreachable')
    comms['band']=Unreachable()
    assert client.post(f"/api/messages/{b['id']}/send").status_code==502
    assert client.app.state.pp.messaging.sent==[]
    assert client.app.state.pp.db.send_state(b['id']) is None


def test_new_clarification_requires_band(client):
    comms=_with_band(client);_sent_batch(client)
    count=len(client.app.state.pp.db.list_records('message_batch'))
    comms['band']=NullBand()
    assert client.post(f'/api/exceptions/{EXC}/clarify').status_code==503
    assert len(client.app.state.pp.db.list_records('message_batch'))==count


def test_handoff_proof_survives_process_recreation(client):
    _with_band(client);draft(client).raise_for_status()
    c2=TestClient(create_app(client.app.state.pp.settings))
    comms=_with_band(c2)
    draft(c2).raise_for_status()
    assert not any('[handoff.requested]' in text for _,text in comms['band'].posts)
    assert any('[decision.requested]' in text for _,text in comms['band'].posts)


def test_legacy_approved_batch_is_not_retroactively_rearmed_or_blocked(client):
    comms=_with_band(client);db=client.app.state.pp.db
    # Existing approval/runtime data has no newly introduced coordination metadata.
    b=draft(client).json()
    stored=db.get_record('message_batch',b['id'])
    legacy={k:v for k,v in stored.items() if k not in {'_version','band_coordination_required','band_decision_message_id','band_room_id'}}
    db.put_record('message_batch',legacy)
    approval(client,b);comms['band']=NullBand()
    r=client.post(f"/api/messages/{b['id']}/send")
    assert r.status_code==200 and r.json()['state']=='sent'
    assert len(client.app.state.pp.messaging.sent)==1
    assert client.post(f"/api/messages/{b['id']}/send").json()['duplicate'] is True
    assert len(client.app.state.pp.messaging.sent)==1


def test_payroll_board_not_completed_without_receipt(monkeypatch):
    import importlib
    orchestration=importlib.import_module("payrollpilot.band.handoff")
    monkeypatch.setattr(orchestration,'_wait_for',lambda *a,**k:None)
    class BoardBand(FakeBand):
        def __init__(self):super().__init__();self.statuses=[]
        def set_status(self,*args):self.statuses.append(args)
    band=BoardBand()
    out=deliver_to_payroll(band,{'id':'exc_test'},{'id':'corr_test','kind':'job_allocation'},'#3',sleep=0)
    assert out['received'] is False and not band.statuses


def test_payroll_route_requires_applied_case_and_dedupes_receipt(client):
    comms=_with_band(client);draft(client).raise_for_status()
    db=client.app.state.pp.db
    db.put_record('resolution',{'id':'res_handoff','exception_id':EXC})
    corr={'id':'corr_handoff','cycle_id':'cyc_mini_v1','state':'proposed','approval_id':None,'resolution_id':'res_handoff','kind':'job_allocation'}
    db.put_record('correction',corr)
    path='/api/corrections/corr_handoff/payroll-handoff'
    assert client.post(path).status_code==409
    db.put_record('correction',{**corr,'state':'applied','approval_id':'appr_existing_owner'})
    comms['band']=NullBand()
    assert client.post(path).status_code==503
    band=FakeBand();comms['band']=band
    out=client.post(path)
    assert out.status_code==200 and out.json()['received'] is True
    count=len(band.posts)
    assert client.post(path).json()['duplicate'] is True
    assert len(band.posts)==count
    assert db.get_record('correction','corr_handoff')['state']=='applied'
    assert client.app.state.pp.messaging.sent==[]


def test_old_band_decision_cannot_approve_an_edited_new_draft(client):
    comms=_with_band(client);b=draft(client).json()
    comms['band'].q.append({'message_id':'human_old','sender_type':'User','content':f"approve {b['id']}"})
    client.post(f"/api/messages/{b['id']}/edit",json={'target_version':b['target_version'],'text':'Changed owner-reviewed wording'}).raise_for_status()
    r=client.post(f"/api/messages/{b['id']}/band-decision")
    assert r.status_code==409 and r.json()['error']=='band_decision_stale'
    assert client.app.state.pp.db.approvals_for_target(b['id'])==[]


def test_phone_request_and_vague_followup_cannot_bypass_band(client):
    from .test_c07_text_approval import _request, _send, _reply
    comms=_with_band(client);target=draft(client).json()
    db=client.app.state.pp.db
    before=len(db.list_records('message_batch'))
    comms['band']=NullBand()
    r=client.post('/api/text-approvals/draft',json={'kind':'message_send','target_id':target['id']})
    assert r.status_code==503 and len(db.list_records('message_batch'))==before
    comms['band']=FakeBand()
    request,code=_request(client,target);_send(client,request)
    count=len(db.list_records('message_batch'))
    comms['band']=NullBand()
    assert _reply(client,'yes').status_code==503
    assert len(db.list_records('message_batch'))==count
    assert db.approvals_for_target(target['id'])==[]
