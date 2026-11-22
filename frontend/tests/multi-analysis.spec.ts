import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';

test('automatic workflow, slide choices, typeset math and complete report on a projector',async({page,request})=>{
 test.setTimeout(240000);
 const p=await(await request.post('/api/v1/projects',{data:{name:'Analisis otomatis - audit'}})).json();
 const lines=['ID,A,B,C,D,E,F,target'];
 for(let i=0;i<180;i++){const y=i%2;const a=Math.sin(i*.43)+y*.25,b=Math.cos(i*.37);const x=Array.from({length:6},(_,j)=>(j<3?.8*a+.1*b:.1*a+.8*b)+.23*Math.sin(i*(j+1)*1.013));lines.push([String(i+1).padStart(3,'0'),...x,y].join(','));}
 const imp=await(await request.post(`/api/v1/projects/${p.id}/imports`,{multipart:{file:{name:'audit-otomatis.csv',mimeType:'text/csv',buffer:Buffer.from(lines.join('\n'))}}})).json();
 await request.post(`/api/v1/imports/${imp.import_id}/confirm`,{data:{decimal:'.'}});
 await page.goto(`/p/${p.id}/analysis/new`);
 await expect(page.getByRole('heading',{name:'Data sumber'})).toBeVisible();
 expect(await page.locator('input,select,textarea').count()).toBe(0);
 await page.screenshot({path:'test-results/automatic-start.png',fullPage:true});
 await page.getByRole('button',{name:'Lanjut',exact:true}).click();
 await expect(page.locator('.automatic-questions>section')).toHaveCount(5);
 await expect(page.getByText('6 indikator',{exact:false})).toBeVisible();
 expect(await page.locator('input,select,textarea').count()).toBe(0);
 let audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(audit.violations).toEqual([]);
 for(const width of [390,768,1366]){await page.setViewportSize({width,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();}
 await page.screenshot({path:'test-results/automatic-plan.png',fullPage:true});
 await page.getByRole('button',{name:'Analisis otomatis',exact:true}).click();
 await expect(page.getByText('Penelaahan selesai.',{exact:false})).toBeVisible({timeout:150000});
 await expect(page.getByRole('link',{name:'Baca rincian hasil',exact:false})).toHaveCount(5);
 audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(audit.violations).toEqual([]);
 await page.screenshot({path:'test-results/automatic-results.png',fullPage:true});
 await page.getByRole('link',{name:'Pilih isi presentasi'}).click();
 await page.getByRole('button',{name:'Susun materi presentasi'}).click();
 await expect(page.locator('.presentation-groups')).toBeVisible();
 const optional=page.getByRole('checkbox',{name:/Dokumentasi teknis lengkap/});await expect(optional).not.toBeChecked();const first=page.locator('.deck-outline input').first();await first.uncheck();await first.check();
 const coreCount=await page.locator('.deck-outline li').count();expect(coreCount).toBeLessThanOrEqual(30);expect(coreCount).toBeGreaterThan(12);
 await page.screenshot({path:'test-results/presentation-choices.png',fullPage:true});
 await page.getByRole('button',{name:'Simpan dan mulai presentasi'}).click();
 await expect(page.locator('.slide>h1')).toBeVisible();
 const sid=page.url().split('/').at(-1);const snapshot=await(await request.get('/api/v1/snapshots/'+sid)).json();
 expect(snapshot.ordered_sections.length).toBe(coreCount);expect(snapshot.ordered_sections.every((s:any)=>s.tier==='core')).toBeTruthy();
 fs.mkdirSync('test-results/multi-report',{recursive:true});fs.writeFileSync('test-results/multi-report/session.json',JSON.stringify({project:p.id,snapshot:sid,sections:snapshot.ordered_sections.length,url:page.url()},null,2));
 await page.setViewportSize({width:1366,height:768});
 const overflows=[];let formulas=0;
 for(let i=0;i<snapshot.ordered_sections.length;i++){
  const section=snapshot.ordered_sections[i];await expect(page.locator('.slide>h1')).toHaveText(section.title);
  if(section.formula||section.paragraphs?.some((p:string)=>p.includes('\\('))){await expect(page.locator('.katex').first()).toBeVisible();formulas++;}
  await page.evaluate(async()=>{await document.fonts.ready;await new Promise(requestAnimationFrame);});
  expect(await page.locator('.katex-error').count()).toBe(0);
  const size=await page.evaluate(()=>({width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight}));
  if(size.height>769||size.width>1367)overflows.push({id:section.id,...size});
  if(i===1||section.id.includes('metric_sensitivity')||section.id.endsWith('_formula')||section.id.endsWith('_conclusion'))await page.screenshot({path:`test-results/multi-report/section-${i}.png`});
  if(i<snapshot.ordered_sections.length-1)await page.getByRole('button',{name:'Bagian berikutnya'}).click();
 }
 fs.writeFileSync('test-results/multi-report/overflows.json',JSON.stringify(overflows,null,2));expect(overflows).toEqual([]);expect(formulas).toBeGreaterThanOrEqual(3);
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
});

test('data without numeric indicators still produces a truthful presentation',async({page,request})=>{
 const p=await(await request.post('/api/v1/projects',{data:{name:'Penjelasan kelayakan - audit'}})).json();
 const imp=await(await request.post(`/api/v1/projects/${p.id}/imports`,{multipart:{file:{name:'nama.csv',mimeType:'text/csv',buffer:Buffer.from('Nama,Kota\nAna,Makassar\nBudi,Balikpapan\nCitra,Manado\n')}}})).json();
 await request.post(`/api/v1/imports/${imp.import_id}/confirm`,{data:{decimal:'.'}});
 await page.goto(`/p/${p.id}/analysis/new`);await page.getByRole('button',{name:'Lanjut',exact:true}).click();
 await page.getByRole('button',{name:'Analisis otomatis',exact:true}).click();
 await expect(page.getByText('Penelaahan selesai.',{exact:false})).toBeVisible();
 await expect(page.getByRole('link',{name:'Baca rincian hasil',exact:false})).toHaveCount(0);
 await page.getByRole('link',{name:'Pilih isi presentasi'}).click();await page.getByRole('button',{name:'Susun materi presentasi'}).click();
 await expect(page.locator('.deck-outline input:checked')).toHaveCount(8);
 await page.getByRole('button',{name:'Simpan dan mulai presentasi'}).click();
 await page.getByRole('button',{name:'Bagian berikutnya'}).click();await expect(page.locator('.slide')).toContainText('bukan hasil estimasi model');
});
