from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code'))
from evidence_layer import Fact
from identity import build_graph
from planner import discover_resources
from main import classify_intent
from policy import load_rules,decide
from state import resource_state

NOW='2026-09-10T12:00:00Z'
def fact(eid,ts,values): return Fact(eid,ts,ts,str(values.get('service','')),str(values.get('resource_id','')),str(values.get('category','')),values,str(values))
def test_cutoff():
 g=build_graph('old@example.test','2026-09-02T00:00:00Z',[{'user_id':'u1','email':'old@example.test','updated_at':'2026-01-01T00:00:00Z'}],[])
 fs=[fact('e1','2026-09-03T00:00:00Z',{'trace_id':'t1','lookup_key':'old@example.test'}),fact('e1','2026-09-03T00:00:01Z',{'trace_id':'t1','resource_id':'account_9','rows':'0','http_status':'404'})]
 assert not discover_resources(g,fs,[], '2026-09-02T23:59:59Z','2026-09-01T00:00:00Z')
def test_historical_email():
 g=build_graph('old@example.test',NOW,[{'user_id':'u2','email':'new@example.test','updated_at':'2026-01-01T00:00:00Z'}],[{'user_id':'u2','field_name':'email','old_value':'old@example.test','new_value':'new@example.test','event_time':'2026-02-01T00:00:00Z'}])
 fs=[fact('e2','2026-09-09T00:00:00Z',{'trace_id':'t2','lookup_key':'old@example.test'}),fact('e2','2026-09-09T00:00:01Z',{'trace_id':'t2','resource_id':'account_22','rows':'0','http_status':'404'})]
 assert 'account_22' in discover_resources(g,fs,[],NOW,'2026-09-08T00:00:00Z')
def test_tombstone_leak():
 g=build_graph('x@example.test',NOW,[{'user_id':'u3','email':'x@example.test','updated_at':'2026-01-01T00:00:00Z'}],[])
 f=fact('e3',NOW,{'resource_id':'tombstone_3','category':'ACCOUNT_TOMBSTONE','user_id':'u3','email':'x@example.test'})
 state=resource_state('tombstone_3',[f],set(g.identifiers),g.user_id,NOW)
 rules=load_rules(ROOT/'dataset'/'deletion_rules.csv')
 assert decide(state,rules).violation == 'identifiers exposed'
def test_claim_not_state():
 g=build_graph('x@example.test',NOW,[{'user_id':'u4','email':'x@example.test','updated_at':'2026-01-01T00:00:00Z'}],[])
 a=[{'activity_id':'a1','event_time':'2026-09-09T00:00:00Z','event_type':'DELETE_RECORD','resource_id':'account_4','details':'Deletion worker reported SUCCESS for account_4'}]
 assert not discover_resources(g,[],a,NOW,'2026-09-08T00:00:00Z')
def test_non_english_non_deletion():
 authorized,reason,_=classify_intent('请导出我的个人数据')
 assert not authorized

cases=[('audit_at cutoff',test_cutoff),('historical email lookup',test_historical_email),('tombstone direct-identifier leak',test_tombstone_leak),('claim is not state evidence',test_claim_not_state),('non-English export is not deletion',test_non_english_non_deletion)]
for name,fn in cases:
 fn(); print('PASS',name)
print(f'{len(cases)}/{len(cases)} passed')

