import io,zipfile
from docx import Document
from pypdf import PdfReader

def extract(data,name):
    chunks=[]
    if name.lower().endswith('.docx'):
        doc=Document(io.BytesIO(data))
        heading=''
        for i,el in enumerate(doc.element.body):
            texts=el.xpath('.//w:t | .//m:t')
            text=' '.join(v.text or '' for v in texts).strip()
            if text:chunks.append(dict(id=f'chunk_{i}',locator=dict(element=i,heading=heading),text=text))
    else:
        reader=PdfReader(io.BytesIO(data))
        if len(reader.pages)>200:raise ValueError('Maksimal 200 halaman PDF.')
        for i,page in enumerate(reader.pages):
            text=page.extract_text() or ''
            if text.strip():chunks.append(dict(id=f'page_{i+1}',locator=dict(page=i+1),text=text))
    return dict(chunks=chunks,status='succeeded' if chunks else 'unavailable',limitation=None if chunks else 'Teks tidak ditemukan; OCR belum tersedia.')

def retrieve(chunks,question):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    if not chunks:return []
    try:matrix=TfidfVectorizer().fit_transform([c['text'] for c in chunks]+[question])
    except ValueError:return []
    score=cosine_similarity(matrix[-1],matrix[:-1]).ravel()
    return [dict(chunks[i],score=float(score[i])) for i in score.argsort()[::-1][:4] if score[i]>0]
