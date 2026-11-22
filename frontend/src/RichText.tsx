import {Fragment,lazy,Suspense} from 'react';
const Inline=lazy(()=>import('./Formula').then(m=>({default:m.InlineFormula})));
export function RichText({text}:{text:string}){const parts=text.split(/\\\((.*?)\\\)/gs);return <>{parts.map((s,i)=>i%2?<Suspense key={i} fallback={<span>Memuat notasi…</span>}><Inline latex={s}/></Suspense>:<Fragment key={i}>{s}</Fragment>)}</>;}
