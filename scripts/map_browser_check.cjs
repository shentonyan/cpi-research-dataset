const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process'),{pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),profile=path.join(root,'work','map-browser-profile'),target=process.env.CPI_MAP_URL||pathToFileURL(path.join(root,'map.html')).href;
fs.mkdirSync(profile,{recursive:true});
const stalePort=path.join(profile,'DevToolsActivePort');if(fs.existsSync(stalePort))fs.unlinkSync(stalePort);
const browser=spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',['--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port=0','--user-data-dir='+profile,target],{windowsHide:true,stdio:'ignore'});
let ws;const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{try{
 const portfile=path.join(profile,'DevToolsActivePort');for(let i=0;i<100&&!fs.existsSync(portfile);i++)await delay(100);
 const port=fs.readFileSync(portfile,'utf8').split('\n')[0];let pages=[];
 for(let i=0;i<100;i++){pages=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();if(pages.some(p=>p.type==='page'&&p.url===target))break;await delay(100)}
 ws=new WebSocket(pages.find(p=>p.type==='page'&&p.url===target).webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
 let id=0;const pending=new Map(),errors=[];
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params);if(pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result)}};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))});
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 await send('Runtime.enable');for(let i=0;i<100;i++){if(await evaluate("document.querySelectorAll('#scene .node').length>0"))break;await delay(100)}
 const checks=[];async function check(name,expression){if(!await evaluate(expression))throw Error('FAILED: '+name);checks.push(name)}
 await check('14 topics rendered from broad corpus',"document.querySelectorAll('#scene .node').length===14 && document.getElementById('map-caption').textContent.includes('714')");
 await check('topic node selects matching source records',"document.querySelector('[data-node=routing]').dispatchEvent(new MouseEvent('click',{bubbles:true}));document.getElementById('selection-title').textContent==='路由与路径' && document.getElementById('paper-count').textContent.includes('113')");
 await check('record search and empty state',"document.getElementById('paper-search').value='__no_such_paper_123__';document.getElementById('paper-search').dispatchEvent(new Event('input'));!!document.querySelector('#paper-list .empty')");
 await evaluate("document.getElementById('paper-search').value='';document.getElementById('paper-search').dispatchEvent(new Event('input'))");
 await check('scope includes 43 core plus 5 context records',"document.getElementById('scope').value='core';document.getElementById('scope').dispatchEvent(new Event('change'));document.getElementById('map-caption').textContent.includes('48') && document.getElementById('paper-count').textContent.includes('48')");
 await check('topic threshold changes visible edge count',"window.edgesBefore=document.querySelectorAll('#scene .edge').length;document.getElementById('threshold').value='20';document.getElementById('threshold').dispatchEvent(new Event('input'));document.querySelectorAll('#scene .edge').length<window.edgesBefore");
 await check('year selection filters papers',"document.querySelector('[data-year=\"2024\"]').click();[...document.querySelectorAll('#paper-list .paper small')].every(x=>x.textContent.includes('2024')) && document.getElementById('paper-count').textContent.includes('2024')");
 await check('citation graph uses 479 nodes and 487 known edges',"document.getElementById('view-citations').click();document.querySelectorAll('#scene .node').length===479 && document.querySelectorAll('#scene .edge').length===487");
 await check('citation selection and directed highlighting',"document.querySelector('#scene .node').dispatchEvent(new MouseEvent('click',{bubbles:true}));!!document.querySelector('#scene .selected') && document.getElementById('selection-label').textContent.includes('SELECTED')");
 await check('zoom modifies viewBox',"window.beforeBox=document.getElementById('network').getAttribute('viewBox');document.getElementById('zoom-in').click();document.getElementById('network').getAttribute('viewBox')!==window.beforeBox");
 await evaluate("document.getElementById('view-topics').click();document.getElementById('scope').value='broad';document.getElementById('scope').dispatchEvent(new Event('change'));document.getElementById('threshold').value='3';document.getElementById('threshold').dispatchEvent(new Event('input'))");
 await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1300,deviceScaleFactor:1,mobile:false});await delay(100);
 await check('desktop has no horizontal overflow',"document.documentElement.scrollWidth<=window.innerWidth");
 let screenshot=await send('Page.captureScreenshot',{format:'png'});const assets=path.join(root,'assets');fs.mkdirSync(assets,{recursive:true});fs.writeFileSync(path.join(assets,'academic-map.png'),Buffer.from(screenshot.data,'base64'));fs.writeFileSync(path.resolve(root,'../../outputs/cpi-academic-map.png'),Buffer.from(screenshot.data,'base64'));
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await delay(100);
 await check('mobile has no horizontal overflow',"document.documentElement.scrollWidth<=window.innerWidth");screenshot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.resolve(root,'../../outputs/cpi-academic-map-mobile.png'),Buffer.from(screenshot.data,'base64'));
 if(errors.length)throw Error('Runtime exceptions: '+JSON.stringify(errors));
 const result={status:'pass',target,browser:'Microsoft Edge headless isolated profile',checks};fs.writeFileSync(path.join(root,'data/processed/map_browser_validation.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));await send('Browser.close');
}finally{if(ws)ws.close();browser.kill()}})().catch(error=>{console.error(error);process.exitCode=1});
