"""Rerun an exported ZIP with this backend installation; never execute uploaded code."""
import argparse,json,zipfile,tempfile
from pathlib import Path
from . import storage as db
from .service import execute

def main():
    parser=argparse.ArgumentParser();parser.add_argument('archive');args=parser.parse_args()
    with zipfile.ZipFile(args.archive) as z:
        manifest=json.loads(z.read('SHA256.json'))
        for name,hash in manifest.items():
            if db.digest(z.read(name))!=hash:raise ValueError('Checksum mismatch: '+name)
        cfg=json.loads(z.read('config.json'));data=json.loads(z.read('dataset.json'));original=json.loads(z.read('results.json'))
    did=db.uid();path=db.folder(did)/'data.json';db.write_json(path,data)
    db.put('dataset',dict(id=did,project_id='reproduction',path=str(path),source_sha256=original['result']['provenance']['source_sha256'],columns=[]))
    cfg['dataset_version_id']=did;run=dict(id=db.uid(),config=cfg);execute(run)
    print(str(db.folder(run['id'])/'result.json'))

if __name__=='__main__':main()
