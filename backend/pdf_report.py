"""Readable PDF using the same frozen sections and figure arrays as the presentation."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .charts import figure

def write_report(path,bundles,sections,source_id):
    font='Helvetica'
    for candidate in ('C:/Windows/Fonts/segoeui.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(candidate).exists():
            font='ReportSans'
            if font not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(font,candidate))
            break
    styles=getSampleStyleSheet()
    for name in ('Title','Heading1','BodyText'):styles[name].fontName=font
    styles['Title'].fontSize=23;styles['Title'].leading=29
    styles['BodyText'].fontSize=13;styles['BodyText'].leading=19
    cell=ParagraphStyle('cell',fontName=font,fontSize=10,leading=14)
    source=ParagraphStyle('source',fontName=font,fontSize=9,leading=13,textColor=colors.HexColor('#52616d'))
    by_run={b['result']['run_id']:b for b in bundles};story=[]
    for index,s in enumerate(sections):
        if index:story.append(PageBreak())
        story.extend([Paragraph(escape(s.get('title','Hasil analisis')),styles['Title']),Spacer(1,16)])
        b=by_run.get(s.get('run_id'))
        if s['kind']=='intro':
            paragraphs=['Analisis multivariat membaca beberapa indikator pada observasi yang sama. PCA merangkum variasi, EFA mengeksplorasi faktor bersama, gerombol mencari kemiripan, dan LDA membedakan label yang diketahui.','Pemilihan metode mengikuti pertanyaan serta kelayakan data.']
        elif s['kind']=='visual' and b:
            image=path.parent/f'figure-{index}.png';plot=figure(b,s['visual_id']);plot.update_layout(title=None,annotations=[],font=dict(size=20),margin=dict(l=85,r=25,t=15,b=80));plot.write_image(str(image));story.append(Image(str(image),width=620,height=366));paragraphs=[next(v['reason_text'] for v in b['result']['visual_manifest'] if v['id']==s['visual_id'])]
        elif s['kind']=='content':paragraphs=s.get('paragraphs',[])
        elif s['kind']=='limits' and b:paragraphs=[d['explanation'] for d in b['result']['diagnostics']]
        else:paragraphs=[n['text'] for n in b['result']['narrative_blocks']] if b else []
        for p in paragraphs:story.extend([Paragraph(escape(p),styles['BodyText']),Spacer(1,10)])
        if s.get('formula'):
            expression=s.get('formula_text') or 'Rumus dan definisi simbol tersedia pada perhitungan analisis ini.'
            story.extend([Paragraph(escape(expression),styles['BodyText']),Spacer(1,12)])
        if s.get('rows'):
            columns=s['columns']
            def text(v):return 'Tidak terdefinisi' if v is None else f'{v:.6g}' if isinstance(v,float) else str(v)
            rows=[[Paragraph(escape(str(c).replace('_',' ')),cell) for c in columns]]+[[Paragraph(escape(text(row.get(c))),cell) for c in columns] for row in s['rows']]
            table=Table(rows,colWidths=[700/len(columns)]*len(columns),repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6f2f1')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d6dee4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
            story.extend([Spacer(1,10),table])
        provenance=b['result']['provenance'] if b else {}
        story.extend([Spacer(1,16),Paragraph(escape(f"Run: {s.get('run_id',source_id)} | sumber SHA256: {provenance.get('source_sha256','pengantar metode')}"),source)])
    def footer(canvas,doc):
        canvas.setFont(font,9);canvas.setFillColor(colors.HexColor('#52616d'));canvas.drawString(36,20,'Multivariat Lab · Hasil komputasi dan batas interpretasi');canvas.drawRightString(805,20,str(doc.page))
    SimpleDocTemplate(str(path),pagesize=landscape(A4),leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=36).build(story,onFirstPage=footer,onLaterPages=footer)
