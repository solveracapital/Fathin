import {useEffect,useRef,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {api,Obj,Visual} from './api';
import {Loading,ErrorBox} from './components';
// Load the chart runtime only when a plot is actually visible.
const loadPlot=()=>import('plotly.js-basic-dist-min');
export default function Plot({runId,item,inline,presentation}:{runId:string,item:Visual,inline?:Obj,presentation?:boolean}){
 const ref=useRef<HTMLDivElement>(null);
 const [plotError,setPlotError]=useState<unknown>();
 const q=useQuery({queryKey:['figure',runId,item.id],queryFn:()=>api(`/runs/${runId}/visuals/${item.id}/figure`),enabled:!inline});
 const source=inline?(inline.figure??figureFromInline(item,inline.data)):q.data;
 useEffect(()=>{let alive=true;let plot:any;let observer:ResizeObserver|undefined;const el=ref.current;
  if(!source||!el)return;
  setPlotError(undefined);
  loadPlot().then(async module=>{if(!alive)return;plot=module.default;const traces=source.data.map((trace:Obj)=>trace.type==='scattergl'?{...trace,type:'scatter'}:trace);await plot.newPlot(el,traces,{...source.layout,title:undefined,width:undefined,height:presentation?360:350,autosize:true,font:{family:'Source Sans 3, Segoe UI, sans-serif',size:presentation?18:14,color:'#18252f'},margin:{l:presentation?80:65,r:24,t:16,b:presentation?90:80},paper_bgcolor:'transparent',plot_bgcolor:'transparent',annotations:[],legend:{orientation:'h',y:-.28,font:{size:presentation?16:13}}},{responsive:false,displaylogo:false,modeBarButtonsToRemove:['toImage','select2d','lasso2d']});if(!alive){plot.purge(el);return;}observer=new ResizeObserver(()=>{if(alive&&el.isConnected&&el.getClientRects().length)plot.Plots.resize(el).catch((e:unknown)=>{if(alive&&el.isConnected)setPlotError(e);});});observer.observe(el);}).catch(e=>{if(alive)setPlotError(e);});
  return()=>{alive=false;observer?.disconnect();if(plot&&el)plot.purge(el);};
 },[source,presentation]);
 if(q.error&&!inline||plotError)return <ErrorBox error={plotError||q.error}/>;
 return <div role="group" aria-label={'Grafik '+item.title} className="plot">{!source&&<Loading/>}<div ref={ref}/></div>;
}
function figureFromInline(item:Visual,d:any):Obj{
 if(item.kind==='scree')return {data:[{x:d.map((x:Obj)=>x.component),y:d.map((x:Obj)=>x.eigenvalue),type:'scatter',mode:'lines+markers',line:{color:'#126b70'}}],layout:{xaxis:{title:{text:'Komponen'}},yaxis:{title:{text:'Eigenvalue'}}}};
 if(item.kind==='scatter')return {data:[{x:d.map((x:Obj)=>x.x),y:d.map((x:Obj)=>x.y),type:'scatter',mode:'markers',marker:{color:'#126b70',size:5,opacity:.5}}],layout:{}};
 if(item.kind==='bar')return {data:(d[0]?.centroid??[]).map((_:any,j:number)=>({type:'bar',x:d.map((x:Obj)=>'Kelompok '+(x.cluster+1)),y:d.map((x:Obj)=>x.centroid[j]),name:'Fitur '+(j+1)})),layout:{}};
 return {data:[{x:d.x,y:d.y,type:'scatter',mode:'lines',line:{color:'#126b70',width:3}}],layout:{xaxis:{title:{text:item.kind==='roc'?'False positive rate':'Recall'}},yaxis:{title:{text:item.kind==='roc'?'Sensitivity':'Precision'}}}};
}
