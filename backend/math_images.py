"""Cached typeset formula assets for ReportLab, using the frontend's KaTeX renderer."""
import json,subprocess,shutil,threading
from . import storage as db
from .mathematics import INLINE
LOCK=threading.Lock()

def prepare_math(sections):
    formulas=set()
    for section in sections:
        if section.get('formula'):formulas.add((section['formula'],True))
        for paragraph in section.get('paragraphs',[]):formulas.update((tex,False) for tex in INLINE.findall(paragraph))
    cache=db.DATA/'math-cache';cache.mkdir(exist_ok=True);assets={};pending=[]
    with LOCK:
        for latex,display in formulas:
            key=db.digest((str(display)+latex).encode());path=cache/(key+'.png');assets[(latex,display)]=path
            if not path.exists() or not path.with_suffix('.png.json').exists():pending.append(dict(latex=latex,display=display,path=str(path)))
        if pending:
            request=cache/(db.uid()+'.json');db.write_json(request,dict(items=pending));node=shutil.which('node')
            if not node:raise ValueError('Node.js diperlukan untuk merender notasi matematika PDF.')
            result=subprocess.run([node,str(db.ROOT/'scripts/render-math.mjs'),str(request)],cwd=db.ROOT,capture_output=True,text=True,timeout=90)
            if result.returncode:raise ValueError('Notasi matematika PDF gagal ditata. '+result.stderr[-500:])
    return {key:dict(path=str(path),**json.loads(path.with_suffix('.png.json').read_text())) for key,path in assets.items()}
