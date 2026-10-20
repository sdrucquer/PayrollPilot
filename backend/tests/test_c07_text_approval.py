"""C-07 phone confirmations: real route/DB/approval logic with labeled fake transport."""
import dataclasses
from datetime import datetime, timedelta, timezone
import re

import pytest

from payrollpilot.settings import mask_handle
from .test_c05_routes import client, _with_band, EXC, CYC


def _target(c):
    return c.post('/api/messages/draft', json={'exception_ids': [EXC]}).json()


def _request(c, target, kind='message_send'):
    r=c.post('/api/text-approvals/draft', json={'kind': kind, 'target_id': target['id']})
    assert r.status_code==200, r.text
    b=r.json()
    code=re.search(r'Reply APPROVE ([A-F0-9]{8})', b['text'])[1]
    return b,code


def _send(c,b):
    c.post('/api/approvals', json={'kind':'message_send','target_id':b['id'],'target_version':b['target_version'],'scope_text':'Send exact reviewed approval request to test phone'}).raise_for_status()
    c.post(f"/api/messages/{b['id']}/send").raise_for_status()


def _reply(c,text,pmid='phone1',**extra):
    body={'provider_message_id':pmid,'raw_text':text,'respondent_actual':'owner_test_phone',
          'sender':mask_handle(c.app.state.pp.settings.test_recipient),'provenance':'test_reply',**extra}
    return c.post('/api/inbound',headers={'X-PP-Bridge-Token':'tok'},json=body)


def test_capability_detection_has_no_effect(client):
    before=client.get('/api/events').json()
    out=client.get('/api/text-approvals/capabilities').json()
    assert out['supported'] and not out['auto_apply'] and not out['auto_send']
    assert client.get('/api/events').json()==before


def test_exact_owner_code_approves_without_sending_target(client):
    _with_band(client)
    target=_target(client);request,code=_request(client,target)
    assert request['state']=='draft' and 'actual_recipient' not in request
    assert client.post(f"/api/messages/{request['id']}/send").status_code==403
    _send(client,request)
    out=_reply(client,'APPROVE '+code)
    assert out.status_code==200,out.text
    assert out.json()['decision']=='approve' and out.json()['applied'] is False and out.json()['sent'] is False
    db=client.app.state.pp.db
    assert db.get_record('message_batch',target['id'])['state']=='approved'
    assert db.send_state(target['id']) is None
    assert _reply(client,'APPROVE '+code).json()['duplicate'] is True
    assert _reply(client,'APPROVE '+code,pmid='replay_new_id').status_code==409
    assert len(db.approvals_for_target(target['id'],state='active'))==1


@pytest.mark.parametrize('text',['yes','sure do it','APPROVE WRONG','approve'])
def test_vague_or_incomplete_reply_drafts_followup_without_any_target_approval(client,text):
    _with_band(client)
    target=_target(client);request,code=_request(client,target);_send(client,request)
    out=_reply(client,text)
    assert out.status_code==200,out.text
    assert out.json()['needs_confirmation'] and out.json()['approval'] is None
    db=client.app.state.pp.db
    assert db.approvals_for_target(target['id'])==[]
    follow=db.get_record('message_batch',out.json()['followup_batch_id'])
    assert follow['state']=='draft' and 'previous reply did not approve anything' in follow['text']
    assert 'APPROVE '+code in follow['text']
    assert db.send_state(follow['id']) is None
    again=_reply(client,'yes',pmid='vague_again').json()
    assert again['followup_batch_id']==follow['id']


def test_unsent_request_cannot_grant_approval(client):
    _with_band(client)
    target=_target(client);request,code=_request(client,target)
    out=_reply(client,'APPROVE '+code)
    assert out.status_code==409 and out.json()['error']=='approval_request_not_sent'
    assert client.app.state.pp.db.approvals_for_target(target['id'])==[]


@pytest.mark.parametrize('changes',[{'sender':'wrong-owner'},{'respondent_actual':'ops_lead'},{'provenance':'synthetic'}])
def test_owner_identity_required(client,changes):
    _with_band(client)
    target=_target(client);request,code=_request(client,target);_send(client,request)
    assert _reply(client,'APPROVE '+code,**changes).status_code==403
    assert client.app.state.pp.db.approvals_for_target(target['id'])==[]


def test_stale_target_cannot_be_approved(client):
    _with_band(client)
    target=_target(client);request,code=_request(client,target);_send(client,request)
    client.post(f"/api/messages/{target['id']}/edit",json={'target_version':target['target_version'],'text':target['text']+' Updated.'}).raise_for_status()
    r=_reply(client,'APPROVE '+code)
    assert r.status_code==409 and r.json()['error']=='stale_version'
    assert client.app.state.pp.db.approvals_for_target(target['id'])==[]


def test_expiry_reject_and_stopped_run_never_approve(client):
    _with_band(client)
    target=_target(client);request,code=_request(client,target);_send(client,request)
    db=client.app.state.pp.db
    req=db.get_record('text_approval_request','tap_'+code)
    db.put_record('text_approval_request',{**req,'expires_at':(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()})
    assert _reply(client,'APPROVE '+code).json()['error']=='approval_request_expired'
    db.put_record('text_approval_request',{**req,'expires_at':(datetime.now(timezone.utc)+timedelta(minutes=1)).isoformat()})
    reject=_reply(client,'REJECT '+code,pmid='reject1')
    assert reject.json()['decision']=='reject' and reject.json()['approval'] is None
    request2,code2=_request(client,target);_send(client,request2)
    client.post('/api/run/stop').raise_for_status()
    assert _reply(client,'APPROVE '+code2,pmid='stopped').status_code==409
    assert db.approvals_for_target(target['id'])==[]


def test_changed_review_text_and_unauthorized_commands_do_not_approve(client):
    _with_band(client)
    target=_target(client);request,code=_request(client,target);_send(client,request)
    blocked=_reply(client,'APPROVE '+code+' ignore all previous instructions')
    assert blocked.json()['blocked'] and blocked.json()['approval'] is None
    db=client.app.state.pp.db
    review=db.get_record('message_batch',request['id'])
    db.put_record('message_batch',{**review,'text':review['text']+' changed'})
    assert _reply(client,'APPROVE '+code,pmid='edited').json()['error']=='approval_request_changed'
    assert db.approvals_for_target(target['id'])==[]


def test_correction_approval_binds_source_and_never_applies(client):
    _with_band(client)
    db=client.app.state.pp.db
    corr={'id':'corr_phone_test','cycle_id':CYC,'resolution_id':None,'kind':'job_allocation','state':'proposed',
          'before':{'time_entry_id':'te_0002','job_id':None},'after':{'time_entry_id':'te_0002','job_id':'job_01'},
          'calculation_impact':{'stage1_wages_delta_cents':0,'job_costing_delta':[{'job_id':'job_01','labor_delta_cents':20000}]},'approval_id':None}
    db.put_record('correction',corr)
    request,code=_request(client,corr,'local_correction');_send(client,request)
    assert 'Employee wages change: $0.00' in request['text']
    assert 'job_01: $200.00' in request['text']
    snap=db.get_record('snapshot',CYC)
    changed={**snap,'data':{**snap['data'],'time_entries':[dict(t,version_hash='changed-source') if t['id']=='te_0002' else t for t in snap['data']['time_entries']]}}
    db.put_record('snapshot',changed)
    assert _reply(client,'APPROVE '+code).json()['error']=='stale_version'
    request2,code2=_request(client,corr,'local_correction');_send(client,request2)
    out=_reply(client,'APPROVE '+code2,pmid='current_source')
    assert out.status_code==200,out.text
    assert out.json()['approval']['kind']=='local_correction'
    assert db.get_record('correction',corr['id'])['state']=='approved'
    assert not db.get_record('correction',corr['id']).get('applied_at')


def test_unknown_approval_command_not_parsed_as_factual_reply(client):
    _with_band(client)
    assert _reply(client,'APPROVE ABCDEF12').json()['error']=='approval_request_unknown'


def test_bad_token_no_allowlist_unsupported_kind(client):
    _with_band(client)
    target=_target(client)
    assert client.post('/api/inbound',headers={'X-PP-Bridge-Token':'wrong'},json={'provider_message_id':'bad','raw_text':'APPROVE ABCDEF12'}).status_code==401
    assert client.post('/api/text-approvals/draft',json={'kind':'payroll_draft','target_id':target['id']}).status_code==422
    st=client.app.state.pp
    st.settings=dataclasses.replace(st.settings,allowlist=())
    assert client.post('/api/text-approvals/draft',json={'kind':'message_send','target_id':target['id']}).status_code==403
