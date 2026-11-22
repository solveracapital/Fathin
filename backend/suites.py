"""Expand independent analyses; never feed the output of one method into another."""
from copy import deepcopy
from . import service,storage as db

def configurations(draft):
    options=draft.get('analysis_options') or {draft['method']:dict(preprocessing=draft.get('preprocessing',{}),settings=draft.get('settings',{}),split=draft.get('split',{}))}
    if not 1<=len(options)<=5 or any(m not in service.METHODS for m in options):raise ValueError('Pilih satu sampai lima metode yang didukung.')
    configs=[]
    for method,option in options.items():
        if not isinstance(option,dict) or set(option)-{'preprocessing','settings','split'}:raise ValueError('Pengaturan metode tidak sah.')
        cfg={k:deepcopy(draft.get(k)) for k in ('dataset_version_id','purpose','feature_ids','target_id','positive_label')}
        cfg.update(method=method,preprocessing=deepcopy(option.get('preprocessing',{})),settings=deepcopy(option.get('settings',{})),split=deepcopy(option.get('split',{})))
        configs.append(cfg)
    return configs

def plan(draft):
    return dict(analyses=[dict(method=c['method'],config=c,**service.validate(c)) for c in configurations(draft)])

def view(suite):
    out=deepcopy(suite)
    for item in out['analyses']:
        if item.get('run_id'):
            r=db.get(item['run_id'],'run');item.update(status=r['status'],error=r.get('error'))
    active=any(i['status'] in ('queued','running') for i in out['analyses'])
    successes=sum(i['status']=='succeeded' for i in out['analyses'])
    answered=sum(i['status']=='explained' for i in out['analyses'])
    out.update(status='running' if active else 'succeeded' if successes+answered==len(out['analyses']) else 'partial' if successes or answered else 'failed',successful_run_ids=[i['run_id'] for i in out['analyses'] if i['status']=='succeeded'])
    return out
