import type { components } from '../../contracts/api';
export type Result = Omit<components['schemas']['AnalysisResult'],'table_index'|'formula_index'|'diagnostics'|'narrative_blocks'|'provenance'> & {table_index:Obj[];formula_index:Obj[];diagnostics:Obj[];narrative_blocks:Obj[];provenance:Obj};
export type Visual = components['schemas']['Visual'];
export type Obj = Record<string, any>;
let token = '';
export async function api<T=Obj>(path:string, init:RequestInit={}):Promise<T> {
  const mutation=init.method && !['GET','HEAD'].includes(init.method);
  if(mutation&&!token){const response=await fetch('/api/v1/health');if(!response.ok)throw new Error('Backend belum dapat dihubungi. Jalankan server lalu coba lagi.');token=(await response.json()).session_token;}
  const headers=new Headers(init.headers);
  if(init.body && !(init.body instanceof FormData))headers.set('Content-Type','application/json');
  if(mutation)headers.set('X-Session-Token',token);
  let response:Response;
  try{response=await fetch('/api/v1'+path,{...init,headers});}catch{throw new Error('Koneksi backend terputus. Periksa server lokal lalu coba lagi.');}
  if(!response.ok){const body=await response.json().catch(()=>({}));if(response.status===403)token='';throw new Error(body.error?.message||'Permintaan belum berhasil. Coba lagi.');}
  return response.json();
}
export const post=<T=Obj>(path:string,body:unknown={})=>api<T>(path,{method:'POST',body:JSON.stringify(body)});
export const patch=<T=Obj>(path:string,body:unknown)=>api<T>(path,{method:'PATCH',body:JSON.stringify(body)});
export const key=()=>crypto.randomUUID();
export const format=(v:any,digits=4):string=>v===null||v===undefined?'Tidak tersedia':typeof v==='number'?new Intl.NumberFormat('id-ID',{maximumFractionDigits:digits}).format(v):typeof v==='object'?JSON.stringify(v):String(v);
export const date=(v:string)=>new Intl.DateTimeFormat('id-ID',{dateStyle:'medium',timeStyle:'short',timeZone:'Asia/Makassar'}).format(new Date(v));
export const methodNames:Record<string,string>={lda:'Analisis diskriminan',pca:'Komponen utama',efa:'Analisis faktor',kmeans:'K-means',hierarchical:'Gerombol hierarkis'};
export const statusNames:Record<string,string>={queued:'Dalam antrean',running:'Sedang dihitung',succeeded:'Selesai',failed:'Gagal',cancelled:'Dibatalkan'};
