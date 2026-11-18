import os,json,sqlite3,uuid,hashlib
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from contextlib import contextmanager

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('MULTIVARIAT_DATA',ROOT/'var')).resolve()
DATA.mkdir(parents=True,exist_ok=True)

def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc).isoformat()
def clean(x):
    if x is pd.NA or x is pd.NaT:return None
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,np.generic):return clean(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    return x
def dumps(x):return json.dumps(clean(x),ensure_ascii=False,allow_nan=False,default=str)
def digest(data):return hashlib.sha256(data).hexdigest()
@contextmanager
def connection():
    c=sqlite3.connect(DATA/'state.sqlite',timeout=30)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('CREATE TABLE IF NOT EXISTS objects (id TEXT PRIMARY KEY, kind TEXT, body TEXT)')
    try:
        with c:yield c
    finally:c.close()
def put(kind,obj):
    obj=clean(obj)
    with connection() as c:c.execute('INSERT OR REPLACE INTO objects VALUES (?,?,?)',(obj['id'],kind,dumps(obj)))
    return obj
def get(id,kind=None):
    with connection() as c:r=c.execute('SELECT kind,body FROM objects WHERE id=?',(id,)).fetchone()
    if not r or (kind and r[0]!=kind):raise KeyError(id)
    return json.loads(r[1])
def listing(kind,project_id=None):
    with connection() as c:rows=c.execute('SELECT body FROM objects WHERE kind=? ORDER BY rowid DESC',(kind,)).fetchall()
    objects=[json.loads(r[0]) for r in rows]
    return [o for o in objects if project_id is None or o.get('project_id')==project_id]
def remove(id):
    with connection() as c:c.execute('DELETE FROM objects WHERE id=?',(id,))
def transition(id,allowed,updates):
    with connection() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT kind,body FROM objects WHERE id=?',(id,)).fetchone()
        if not row:return None
        obj=json.loads(row[1])
        if obj.get('status') not in allowed:return None
        obj.update(clean(updates));c.execute('UPDATE objects SET body=? WHERE id=?',(dumps(obj),id))
        return obj
def folder(id):
    try:uuid.UUID(id)
    except (ValueError,TypeError,AttributeError):raise ValueError('ID tidak valid.')
    p=DATA/id;p.mkdir(exist_ok=True);return p
def write_json(path,data):
    temp=path.with_name(path.name+'.'+uid()+'.tmp');temp.write_text(dumps(data),encoding='utf-8');temp.replace(path)
