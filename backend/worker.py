"""One subprocess per job: parent can stop numerical work and R process tree."""
import sys,traceback
from . import storage as db
from .service import execute

if __name__=='__main__':
    job=db.transition(sys.argv[1],['queued'],dict(status='running',phase='fitting',progress=None,started_at=db.now()))
    if job is None:sys.exit(0)
    try:
        provenance=execute(job)
        job.update(status='succeeded',phase='building_results',progress=None,finished_at=db.now(),provenance=provenance,error=None)
    except Exception as e:
        job.update(status='failed',finished_at=db.now(),error=dict(code='ANALYSIS_FAILED',message=str(e) if isinstance(e,ValueError) else 'Analisis gagal. Periksa konfigurasi atau dependensi.',retryable=False))
        (db.folder(job['id'])/'developer.log').write_text(traceback.format_exc(),encoding='utf-8')
    db.transition(job['id'],['running'],job)
