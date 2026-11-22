import plotly.graph_objects as go
import numpy as np
from scipy.cluster.hierarchy import dendrogram

def figure(bundle,id):
    item=next(v for v in bundle['result']['visual_manifest'] if v['id']==id)
    data=bundle['visuals'][id]['data'];kind=item['kind'];fig=go.Figure();names=bundle['result']['provenance'].get('feature_labels',[])
    if kind=='confusion_matrix':
        fig.add_trace(go.Heatmap(z=data['matrix'],x=['Prediksi negatif','Prediksi positif'],y=['Aktual negatif','Aktual positif'],text=data['matrix'],texttemplate='%{text}',colorscale='Blues',showscale=False))
        fig.update_yaxes(autorange='reversed',title='Kelas aktual');fig.update_xaxes(title='Prediksi')
    elif kind in ('roc','precision_recall'):
        fig.add_trace(go.Scatter(x=data['x'],y=data['y'],mode='lines',line=dict(color='#126B70',width=3,shape='hv' if kind=='precision_recall' else 'linear')))
        fig.update_xaxes(title='False positive rate' if kind=='roc' else 'Recall',range=[0,1])
        fig.update_yaxes(title='Sensitivity' if kind=='roc' else 'Precision',range=[0,1.02])
    elif kind=='scree':
        fig.add_trace(go.Scatter(x=[v['component'] for v in data],y=[v['eigenvalue'] for v in data],mode='lines+markers'))
        fig.update_xaxes(title='Komponen');fig.update_yaxes(title='Eigenvalue')
    elif kind=='scatter':
        fig.add_trace(go.Scatter(x=[v['x'] for v in data],y=[v['y'] for v in data],mode='markers'))
        projection=item.get('projection') or {};pve=projection.get('explained_variance',[0,0]);fig.update_xaxes(title=f'PC1 ({100*pve[0]:.2f}% variasi)');fig.update_yaxes(title=f'PC2 ({100*pve[1]:.2f}% variasi)')
    elif kind=='heatmap':
        bound=max(1.,float(np.max(np.abs([v['pattern'] for v in data]))))
        fig.add_trace(go.Heatmap(z=[v['pattern'] for v in data],x=[f'Faktor {i+1}' for i in range(len(data[0]['pattern']))],y=[v.get('label',v['feature']) for v in data],colorscale='RdBu',zmid=0,zmin=-bound,zmax=bound,colorbar=dict(title='Pattern')))
        fig.update_yaxes(autorange='reversed')
    elif kind=='bar':
        for j in range(len(data[0]['centroid'])):fig.add_trace(go.Bar(x=[f"Kelompok {v['cluster']+1}" for v in data],y=[v['centroid'][j] for v in data],name=names[j] if j<len(names) else f'Fitur {j+1}'))
        fig.update_yaxes(title='Pusat pada skala pengolahan');fig.update_xaxes(title='Kelompok (bukan peringkat risiko)')
    elif kind=='dendrogram':
        d=dendrogram(np.array(data['linkage']),truncate_mode='lastp',p=30,no_plot=True)
        for x,y in zip(d['icoord'],d['dcoord']):fig.add_trace(go.Scatter(x=x,y=y,mode='lines',showlegend=False))
        fig.update_xaxes(tickmode='array',tickvals=list(range(5,10*len(d['ivl'])+5,10)),ticktext=d['ivl'],title='Nomor observasi / (jumlah anggota cabang)');fig.update_yaxes(title='Tinggi penggabungan')
    elif kind=='line':
        for k in ('observed','simulated'):
            if k in data:fig.add_trace(go.Scatter(x=list(range(1,len(data[k])+1)),y=data[k],name='Data teramati' if k=='observed' else 'Batas acak 95%',line=dict(dash='solid' if k=='observed' else 'dash')))
        fig.update_xaxes(title='Urutan faktor',dtick=max(1,int(np.ceil(len(data['observed'])/15))));fig.update_yaxes(title='Eigenvalue faktor bersama')
    else:raise ValueError('Renderer visual belum tersedia.')
    n=bundle['result']['subset_definitions'].get(item['subset_id'],{}).get('n')
    fig.update_layout(title=item['title'],colorway=['#126B70','#365EA8','#A65B1A','#7D4F96','#64723C','#986058'],template='plotly_white',font=dict(family='Arial',size=16),width=1100,height=650,margin=dict(b=110),annotations=[dict(text=f"Subset: {item['subset_id']} | n={n} | Run: {bundle['result']['run_id']}<br>{item['reason_text']}",xref='paper',yref='paper',x=0,y=-.17,showarrow=False,xanchor='left',font=dict(size=11))])
    return fig
