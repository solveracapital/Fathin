import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
let project:string,lda:string,pca:string;
const extra:Record<string,string>={};
async function finished(request:any,draft:string){
 const response=await request.post('/api/v1/runs',{data:{draft_id:draft,revision:1,idempotency_key:crypto.randomUUID()}});expect(response.status(),await response.text()).toBe(202);const start=await response.json();
 for(let i=0;i<450;i++){const r=await(await request.get('/api/v1/runs/'+start.run_id)).json();if(r.status==='succeeded')return start.run_id;if(r.status==='failed')throw new Error(JSON.stringify(r));await new Promise(r=>setTimeout(r,200));}
 throw new Error('Run did not finish');
}
test.beforeAll(async({request})=>{
 project=(await(await request.post('/api/v1/projects',{data:{name:'Audit sistem menyeluruh'}})).json()).id;
 const example=await(await request.post(`/api/v1/projects/${project}/case-study`)).json();
 lda=await finished(request,example.draft_ids[0]);pca=await finished(request,example.draft_ids[1]);
 const names=['Likuiditas','Profitabilitas','Efisiensi','Utang','Modal','ArusKas'];
 const lines=[names.join(',')];
 for(let i=0;i<140;i++){const a=Math.sin(i*.41),b=Math.cos(i*.29);lines.push(names.map((_,j)=>((j<3?.8*a+.1*b:.1*a+.8*b)+.23*Math.sin(i*(j+1)*1.013)).toString()).join(','));}
 const imp=await(await request.post(`/api/v1/projects/${project}/imports`,{multipart:{file:{name:'indikator-sintetis.csv',mimeType:'text/csv',buffer:Buffer.from(lines.join('\n'))}}})).json();
 const ds=await(await request.post(`/api/v1/imports/${imp.import_id}/confirm`,{data:{decimal:'.',header_row:1}})).json();
 for(const method of ['kmeans','hierarchical','efa']){
  const d=await(await request.post(`/api/v1/projects/${project}/drafts`,{data:{dataset_version_id:ds.id,method,purpose:'Audit sintetis '+method,feature_ids:ds.columns.map((c:any)=>c.id),settings:method==='efa'?{q:2,extraction:'pa',rotation:'oblimin'}:{k:3},preprocessing:{scale:'standard'},split:{seed:42}}})).json();
  extra[method]=await finished(request,d.id);
 }
 fs.mkdirSync('test-results/system-audit',{recursive:true});
 fs.writeFileSync('test-results/system-audit/ids.json',JSON.stringify({project,lda,pca,extra},null,2));
});
test('PCA renders real SVG points and the saved scores match the plot',async({page,request})=>{
 await page.goto(`/p/${project}/results/${pca}/summary`);
 await page.getByText('Visual tambahan yang relevan',{exact:true}).click();
 await page.getByRole('checkbox',{name:/Proyeksi skor PCA/}).check();
 const plot=page.locator('.plot').last();await expect(plot.locator('.scatterlayer .points path.point').first()).toBeVisible();
 const actual=await(await request.get(`/api/v1/runs/${pca}/visuals/scores`)).json();
 const rendered=await plot.locator('.js-plotly-plot').evaluate((el:any)=>({type:el.data[0].type,x:el.data[0].x,y:el.data[0].y}));
 expect(rendered.type).toBe('scatter');expect(rendered.x).toEqual(actual.data.map((r:any)=>r.x));expect(rendered.y).toEqual(actual.data.map((r:any)=>r.y));
 await page.screenshot({path:'test-results/system-audit/pca.png',fullPage:true});
});
test('all clustering and factor visuals have real data, labels and readable alternatives',async({page,request})=>{
 const browserErrors:string[]=[];page.on('pageerror',e=>browserErrors.push(e.message));
 for(const method of ['kmeans','hierarchical','efa']){
  await page.goto(`/p/${project}/results/${extra[method]}/summary`);
  await expect(page.getByRole('heading',{name:'Apa yang ditemukan?'})).toBeVisible();
  if(method==='efa'){await expect(page.getByRole('region',{name:'Loading faktor'})).toContainText('Likuiditas');}
  else{await expect(page.locator('.barlayer .trace').first()).toBeVisible();await expect(page.locator('.plot').first()).toContainText('Likuiditas');}
  const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).disableRules(['region']).analyze();
  expect(audit.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))).toEqual([]);
  await page.screenshot({path:`test-results/system-audit/${method}.png`,fullPage:true});
  await page.setViewportSize({width:390,height:844});await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();await page.setViewportSize({width:1440,height:900});
  const observation=await(await request.get(`/api/v1/runs/${extra[method]}/observations/1`)).json();
  const table=await(await request.get(`/api/v1/runs/${extra[method]}/tables/${method==='efa'?'factor_scores':'membership'}`)).json();
  if(method==='efa')expect(observation.scores).toEqual(table.items[0].values);
  else expect(observation.cluster).toEqual(table.items[0].cluster);
  await page.getByRole('link',{name:'Observasi',exact:true}).click();await page.getByRole('button',{name:'Buka',exact:true}).first().click();
  await expect(page.getByRole('dialog')).toContainText(method==='efa'?'Faktor 1':'Keanggotaan');await page.getByRole('button',{name:'Tutup',exact:true}).click();
 }
 expect(browserErrors).toEqual([]);
});
test('every presentation section fits a projector viewport and preserves the complete story',async({page,request})=>{
 const a=await(await request.get(`/api/v1/runs/${lda}/presentation`)).json();const b=await(await request.get(`/api/v1/runs/${pca}/presentation`)).json();
 const sections=[...a.sections,...b.sections];
 const snapshot=await(await request.post(`/api/v1/projects/${project}/snapshots`,{data:{run_ids:[lda,pca],ordered_sections:sections}})).json();
 expect(snapshot.ordered_sections.some((s:any)=>s.id.endsWith('_formula'))).toBeTruthy();
 expect(snapshot.ordered_sections.some((s:any)=>s.id.endsWith('_decisions'))).toBeTruthy();
 await page.setViewportSize({width:1366,height:768});await page.goto('/present/'+snapshot.id);
 const measurements=[];
 for(let i=0;i<sections.length;i++){
  await expect(page.locator('.slide>h1')).toHaveText(sections[i].title);
  const dimensions=await page.evaluate(()=>({height:document.documentElement.scrollHeight,width:document.documentElement.scrollWidth,viewportH:innerHeight,viewportW:innerWidth}));
  measurements.push({id:sections[i].id,...dimensions});
  expect(dimensions.height,sections[i].id).toBeLessThanOrEqual(769);expect(dimensions.width).toBeLessThanOrEqual(1367);
  if(['_example','_formula','_decisions','_variables','_scree'].some(k=>sections[i].id.endsWith(k)))await page.screenshot({path:`test-results/system-audit/slide-${i}.png`,fullPage:true});
  if(i<sections.length-1)await page.getByRole('button',{name:'Bagian berikutnya'}).click();
 }
 fs.writeFileSync('test-results/system-audit/projector-measurements.json',JSON.stringify(measurements,null,2));
});
