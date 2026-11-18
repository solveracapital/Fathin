import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
let project:string,runId:string,pca:string,dataset:string;
test.beforeAll(async({request})=>{
 const p=await (await request.post('/api/v1/projects',{data:{name:'Vérifikasi antarmuka',description:'Proyek pengujian frontend'}})).json();project=p.id;
 const sample=await (await request.post(`/api/v1/projects/${project}/case-study`)).json();dataset=sample.dataset_id;
 const runs=[];
 for(const d of sample.draft_ids){const start=await(await request.post('/api/v1/runs',{data:{draft_id:d,revision:1,idempotency_key:crypto.randomUUID()}})).json();
  for(let i=0;i<300;i++){const r=await(await request.get('/api/v1/runs/'+start.run_id)).json();if(r.status==='succeeded')break;if(r.status==='failed')throw new Error(JSON.stringify(r));await new Promise(r=>setTimeout(r,200));}runs.push(start.run_id);}
 [runId,pca]=runs;
 fs.mkdirSync('test-results/screenshots',{recursive:true});
});
test('LDA result, observation, threshold, export, and presentation',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(`/p/${project}/results/${runId}/summary`);
 await expect(page.getByRole('heading',{name:'Apa yang ditemukan?'})).toBeVisible();
 await expect(page.getByText('Dari 66 kasus positif test, 12 terdeteksi dan 54 terlewat.',{exact:false})).toBeVisible();
 await page.getByLabel('Skenario',{exact:true}).selectOption('oof_threshold');
 await expect(page.locator('.scenario-counts strong').first()).toHaveText('28');
 await page.getByRole('link',{name:'Observasi',exact:true}).click();
 await page.getByLabel('Identitas baris').fill('TW03598');await page.getByRole('button',{name:'Telusuri',exact:true}).click();
 const dialog=page.getByRole('dialog');await expect(dialog).toContainText('0,9934229407');
 await page.getByRole('button',{name:'Tutup',exact:true}).click();
 await page.getByRole('link',{name:'Ringkasan',exact:true}).click();
 await page.getByRole('button',{name:'Ekspor',exact:true}).click();await page.getByLabel('Format',{exact:true}).selectOption('csv');
 await page.getByRole('button',{name:'Siapkan berkas'}).click();await expect(page.getByRole('link',{name:'Unduh CSV'})).toBeVisible();await page.getByRole('button',{name:'Tutup',exact:true}).click();
 await page.getByRole('link',{name:'Presentasikan',exact:true}).click();await page.getByRole('button',{name:'Siapkan alur presentasi'}).click();
 await expect(page.getByRole('heading',{name:'Urutan cerita'})).toBeVisible();await page.getByRole('button',{name:'Simpan dan mulai presentasi'}).click();
 await expect(page).toHaveURL(/\/present\//);await expect(page.locator('.slide')).toBeVisible();
 await page.getByRole('button',{name:'Bagian berikutnya'}).click();await page.getByRole('button',{name:'Bagian berikutnya'}).click();
 await page.screenshot({path:'test-results/screenshots/presentation.png',fullPage:true});
 expect(errors).toEqual([]);
});
test('CSV upload, mapping and PCA wizard',async({page})=>{
 await page.goto(`/p/${project}/data`);
 await page.locator('input[type=file]').setInputFiles({name:'contoh.csv',mimeType:'text/csv',buffer:Buffer.from('ID,A,B,C\n001,1,2,2\n002,2,3,1\n003,3,5,4\n004,4,4,3\n005,5,6,2\n006,6,8,5\n')});
 await expect(page.getByRole('heading',{name:'Periksa pengaturan impor'})).toBeVisible();
 await page.getByRole('button',{name:'Konfirmasi impor'}).click();await expect(page.getByRole('heading',{name:'Peran dan definisi kolom'})).toBeVisible();
 await page.getByLabel('Peran ID',{exact:true}).selectOption('id');await page.getByRole('button',{name:'Simpan pemetaan'}).click();
 await expect(page.getByRole('heading',{name:'Data',exact:true})).toBeVisible();
 await page.getByRole('link',{name:'Rancang analisis',exact:true}).last().click();
 await expect(page.getByRole('heading',{name:'Pertanyaan apa yang ingin dijawab?'})).toBeVisible();await page.getByRole('button',{name:'Lanjut',exact:true}).click();
 for(const col of ['A','B','C'])await page.locator('.feature-list').getByRole('checkbox',{name:new RegExp('^'+col+'Skala|^'+col+' Skala')}).check().catch(async()=>{await page.locator('.feature-list label').filter({hasText:new RegExp('^'+col)}).getByRole('checkbox').check();});
 await page.getByRole('button',{name:'Lanjut',exact:true}).click();await page.getByRole('button',{name:'Lanjut',exact:true}).click();
 await expect(page.getByText('Konfigurasi lolos pemeriksaan awal.',{exact:false})).toBeVisible();await page.getByRole('button',{name:'Jalankan analisis',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Apa yang ditemukan?'})).toBeVisible({timeout:60000});
 await expect(page.getByRole('heading',{name:'Kasus yang terdeteksi dan terlewat'})).toHaveCount(0);
});
test('responsive layout, keyboard access and accessibility',async({page})=>{
 await page.goto(`/p/${project}/results/${runId}/summary`);await expect(page.getByRole('heading',{name:'Apa yang ditemukan?'})).toBeVisible();
 const issues=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).disableRules(['region']).analyze();
 expect(issues.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))).toEqual([]);
 for(const width of [320,390,768,1024,1366,1440,1920]){
  await page.setViewportSize({width,height:900});await page.waitForTimeout(150);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
  if([390,1440].includes(width))await page.screenshot({path:`test-results/screenshots/results-${width}.png`,fullPage:true});
 }
 await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'Buka navigasi'}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.goto('/');await page.setViewportSize({width:1440,height:900});await expect(page.getByRole('heading',{name:'Dari data menuju pemahaman.'})).toBeVisible();await page.screenshot({path:'test-results/screenshots/home.png',fullPage:true});
});

test('document reading, local evidence and unavailable AI',async({page})=>{
 await page.goto(`/p/${project}/documents`);
 await page.locator('input[type=file]').setInputFiles('../outputs/makalah_multivariat/Makalah_Analisis_Multivariat.docx');
 await expect(page.getByRole('button',{name:/Makalah_Analisis_Multivariat.docx/})).toBeVisible({timeout:20000});
 await page.getByRole('button',{name:'Cari penjelasan dari dokumen'}).click();
 await page.getByLabel('Pertanyaan',{exact:true}).fill('Analisis diskriminan dan akurasi');
 await page.getByRole('button',{name:'Jelaskan dengan bukti'}).click();
 await expect(page.locator('.assistant-answer blockquote').first()).toBeVisible();
 await page.getByRole('button',{name:'Tutup',exact:true}).click();
 await page.getByRole('button',{name:/Makalah_Analisis_Multivariat.docx/}).click();
 await page.getByRole('button',{name:'Identifikasi metode yang dibahas'}).click();
 await expect(page.getByText('Kandidat:',{exact:false})).toBeVisible();
});

test('saved presentation remains readable when snapshot API is unavailable',async({page,request})=>{
 const snap=await(await request.post(`/api/v1/projects/${project}/snapshots`,{data:{run_ids:[runId]}})).json();
 await page.goto(`/present/${snap.id}`);await expect(page.locator('.slide-prose')).toContainText('Dari 66 kasus positif test');
 await page.route('**/api/v1/snapshots/**',route=>route.abort());
 await page.reload();await expect(page.locator('.slide-prose')).toContainText('Dari 66 kasus positif test');
});
