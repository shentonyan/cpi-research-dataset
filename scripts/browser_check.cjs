// Integration checks in a fresh, isolated, headless Edge profile. No npm deps.
const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process'),{pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),profile=path.join(root,'work','browser-check-profile');
fs.mkdirSync(profile,{recursive:true});
const stalePort=path.join(profile,'DevToolsActivePort');if(fs.existsSync(stalePort))fs.unlinkSync(stalePort);
const browser=spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',['--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port=0','--user-data-dir='+profile,pathToFileURL(path.join(root,'index.html')).href],{windowsHide:true,stdio:'ignore'});
let ws;
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 try{
  const portfile=path.join(profile,'DevToolsActivePort');
  for(let i=0;i<100&&!fs.existsSync(portfile);i++)await delay(100);
  const port=fs.readFileSync(portfile,'utf8').split('\n')[0];
  let pages=[];
  for(let i=0;i<100;i++){pages=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();if(pages.some(p=>p.type==='page'&&p.url.includes('index.html')))break;await delay(100);}
  const page=pages.find(p=>p.type==='page'&&p.url.includes('index.html'));
  ws=new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
  let id=0;const pending=new Map();
  ws.onmessage=event=>{const message=JSON.parse(event.data);if(pending.has(message.id)){const p=pending.get(message.id);pending.delete(message.id);message.error?p.reject(message.error):p.resolve(message.result)}};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))});
  const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
  for(let i=0;i<100;i++){if(await evaluate("document.querySelectorAll('.record').length>0"))break;await delay(100);}
  const checks=[];
  async function check(name,expression){if(!await evaluate(expression))throw Error('FAILED: '+name);checks.push(name)}
  await check('initial core scope and count',"document.querySelectorAll('.record').length===43 && document.getElementById('count').textContent.includes('43')");
  await check('case-insensitive DOI retrieval',"document.getElementById('query').value='10.1016/J.CIE.2024.110293';document.getElementById('query').dispatchEvent(new Event('input'));document.querySelectorAll('.record').length===1");
  await check('empty-state search',"document.getElementById('query').value='__no_such_paper_123__';document.getElementById('query').dispatchEvent(new Event('input'));document.querySelectorAll('.record').length===0 && !!document.querySelector('.empty')");
  await check('collection and pagination',"document.getElementById('query').value='';document.getElementById('query').dispatchEvent(new Event('input'));document.querySelector('[data-scope=all]').click();document.querySelectorAll('.record').length===60 && !document.getElementById('more').hidden");
  await check('load more',"document.getElementById('more').click();document.querySelectorAll('.record').length===120");
  await check('year filter',"document.getElementById('year').value='2024';document.getElementById('year').dispatchEvent(new Event('change'));[...document.querySelectorAll('.record .meta')].every(x=>x.textContent.includes('2024'))");
  await evaluate("document.getElementById('year').value='';document.getElementById('year').dispatchEvent(new Event('change'));document.querySelector('[data-scope=core_cpi]').click()");
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await check('mobile viewport has no horizontal overflow',"document.documentElement.scrollWidth<=window.innerWidth");
  const screenshot=await send('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.resolve(root,'../../outputs/cpi-research-mobile.png'),Buffer.from(screenshot.data,'base64'));
  const result={status:'pass',browser:'Microsoft Edge headless, isolated profile',checks};
  fs.writeFileSync(path.join(root,'data/processed/browser_validation.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
  await send('Browser.close');
 }finally{if(ws)ws.close();browser.kill();}
})().catch(error=>{console.error(error);process.exitCode=1});
