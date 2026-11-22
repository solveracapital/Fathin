// Render the same local KaTeX fonts used by the frontend. No remote resources.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import katex from '../frontend/node_modules/katex/dist/katex.mjs';
import {chromium} from '../frontend/node_modules/playwright-core/index.mjs';
const request=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const css=pathToFileURL(path.resolve('frontend/node_modules/katex/dist/katex.min.css')).href;
const html=request.items.map((m,i)=>`<div id="m${i}" class="math ${m.display?'block':'inline'}">${katex.renderToString(m.latex,{displayMode:m.display,throwOnError:true,trust:false,maxExpand:1000,maxSize:20})}</div>`).join('');
const file=process.argv[2]+'.html';
fs.writeFileSync(file,`<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="${css}"><style>body{margin:0;background:white;color:#18252f}.math{width:max-content;padding:5px 3px;margin:0}.block{font-size:22px}.inline{font-size:17px}.katex-display{margin:0}</style>${html}`);
const channel=fs.existsSync('C:/Program Files/Google/Chrome/Application/chrome.exe')?'chrome':fs.existsSync('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')?'msedge':undefined;
const browser=await chromium.launch({channel,headless:true});
try{
 const page=await browser.newPage({viewport:{width:1800,height:1000},deviceScaleFactor:2});await page.goto(pathToFileURL(file).href);await page.evaluate(()=>document.fonts.ready);
 for(let i=0;i<request.items.length;i++){const el=page.locator('#m'+i);const size=await el.boundingBox();await el.screenshot({path:request.items[i].path});fs.writeFileSync(request.items[i].path+'.json',JSON.stringify({width:size.width*.75,height:size.height*.75}));}
}finally{await browser.close();}
