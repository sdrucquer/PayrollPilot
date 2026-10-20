import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import bundle from '../src/fixtures/bundle.ts'
const {chromium}=createRequire(import.meta.url)(process.env.PP_PLAYWRIGHT_MODULE ?? 'playwright')
const b=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true})
const p=await b.newPage()
const issues=bundle.exceptions.filter(e=>e.intended_respondent_role==='ops_lead').slice(0,2).map(e=>({...e,state:'detected',owner_agent:'audit',message_ids:[]}))
const posts=[],errors=[]; let failSecond=true, failSend=false, batch=null
p.on('pageerror',e=>errors.push(e.message))
await p.route('**/api/**',async route=>{
 const req=route.request(),path=new URL(req.url()).pathname
 if(req.method()==='POST'){
  posts.push(path)
  const handoff=issues.find(e=>path===`/api/exceptions/${e.id}/handoff`)
  if(handoff){if(failSend||(failSecond&&handoff===issues[1]))return route.fulfill({status:503,json:{error:'band_required'}});handoff.owner_agent='resolution';return route.fulfill({json:{exception:handoff}})}
  if(path==='/api/messages/draft'){batch={id:'guard-batch',cycle_id:bundle.cycle.id,exception_ids:issues.map(e=>e.id),text:'Which job were these shifts on?',text_hash:'sha256:exact',state:'draft',approval_id:null,intended_respondent_role:'ops_lead',intended_respondent_label:'Ops lead',actual_recipient_masked:'***-**12',provenance:'synthetic'};return route.fulfill({json:batch})}
  if(path==='/api/approvals'){batch.state='approved';batch.approval_id='owner-approved';return route.fulfill({json:{id:'owner-approved'}})}
  if(path==='/api/messages/guard-batch/send'){batch.state='sent';return route.fulfill({json:batch})}
  return route.fulfill({status:500,json:{error:'unexpected_post'}})
 }
 let body
 if(path===`/api/cycles/${bundle.cycle.id}`)body=bundle.cycle
 else if(path.endsWith('/readiness'))body=bundle.readiness
 else if(path.endsWith('/exceptions'))body=issues
 else if(path.endsWith('/packet'))body=null
 else if(path==='/api/events')body=[]
 else if(path==='/api/health')body={...bundle.health,adapters:{messaging:{mode:'fake'}}}
 else {const e=issues.find(e=>path===`/api/exceptions/${e.id}`);if(e)body={...e,messages:{outbound:batch?[batch]:[],inbound:[]},correction:null};else return route.fulfill({status:404,json:{error:'not_found'}})}
 return route.fulfill({json:body})
})
try{
 await p.goto(process.env.PP_QA_WEB??'http://127.0.0.1:5174/')
 await p.getByRole('button',{name:'Draft message',exact:true}).click()
 await p.getByRole('alert').filter({hasText:'band_required'}).waitFor()
 assert.equal(posts.includes('/api/messages/draft'),false)
 assert.equal(posts.includes('/api/approvals'),false)
 assert.equal(issues[0].owner_agent,'resolution')
 failSecond=false
 await p.getByRole('button',{name:'Draft message',exact:true}).click()
 await p.getByRole('button',{name:'Approve & send',exact:true}).waitFor()
 assert.equal(posts.filter(x=>x===`/api/exceptions/${issues[0].id}/handoff`).length,1,'persisted ownership skips repeat handoff')
 issues[0].owner_agent='audit';failSend=true
 await p.getByRole('button',{name:'Approve & send',exact:true}).click()
 await p.getByRole('alert').filter({hasText:'band_required'}).waitFor()
 assert.equal(posts.includes('/api/approvals'),false,'failed preflight creates no approval')
 assert.equal(posts.includes('/api/messages/guard-batch/send'),false)
 failSend=false
 await p.getByRole('button',{name:'Approve & send',exact:true}).click()
 await p.locator('.h-toast').filter({hasText:'Sent to the Ops lead.'}).waitFor()
 assert.ok(posts.lastIndexOf(`/api/exceptions/${issues[0].id}/handoff`)<posts.indexOf('/api/approvals'))
 assert.ok(posts.indexOf('/api/approvals')<posts.indexOf('/api/messages/guard-batch/send'))
 assert.deepEqual(errors,[])
 console.log('Band browser checks passed: failed grouped handoff blocks draft, retry skips persisted ownership, failed send preflight creates no approval/send, successful order is handoff -> approval -> send.')
}finally{await b.close()}
