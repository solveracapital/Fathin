import {defineConfig} from '@playwright/test';
import {existsSync} from 'node:fs';
const channel=process.env.PLAYWRIGHT_CHANNEL||(existsSync('C:/Program Files/Google/Chrome/Application/chrome.exe')?'chrome':undefined);
export default defineConfig({testDir:'tests',timeout:120000,workers:1,use:{baseURL:'http://127.0.0.1:5173',viewport:{width:1440,height:900},headless:true,channel},reporter:[['list'],['json',{outputFile:'test-results/report.json'}]],outputDir:'test-results/artifacts'});
