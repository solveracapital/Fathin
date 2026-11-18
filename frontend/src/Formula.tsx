import katex from 'katex';
import 'katex/dist/katex.min.css';
export default function Formula({latex}:{latex:string}){return <div className="formula" role="math" aria-label={latex} dangerouslySetInnerHTML={{__html:katex.renderToString(latex,{throwOnError:false,trust:false,displayMode:true})}}/>;}
