// Node 22+; a dedicated headless Chrome must expose localhost:9237.
// Uses the Chrome DevTools Protocol directly: no npm packages or external services.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const endpoint=process.env.CHROME_DEBUG_URL||'http://127.0.0.1:9237';
const base=process.env.DEMO_URL||'http://127.0.0.1:8787';
const targets=await (await fetch(endpoint+'/json/list')).json();
const target=targets.find(tab=>tab.type==='page');
if(!target)throw new Error('Open a dedicated headless Chrome tab first.');
const socket=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
let serial=0;
const pending=new Map(), errors=[];
socket.onmessage=event=>{
  const message=JSON.parse(event.data);
  if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails.text);
  if(message.id&&pending.has(message.id)){
    const {resolve,reject}=pending.get(message.id);pending.delete(message.id);
    message.error?reject(new Error(message.error.message)):resolve(message.result);
  }
};
function command(method,params={}){
  return new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
}
async function evaluate(expression){
  const response=await command('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
  if(response.exceptionDetails)throw new Error(response.exceptionDetails.text);
  return response.result.value;
}
async function waitFor(expression){
  const deadline=Date.now()+12000;
  while(Date.now()<deadline){
    if(await evaluate(expression))return;
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  throw new Error('UI condition timed out: '+expression);
}
async function navigate(url){
  await command('Page.navigate',{url});
  await waitFor('document.readyState==="complete" && document.querySelectorAll(".result-row").length===3');
  await evaluate('document.fonts.ready.then(()=>true)');
}
async function capture(name){
  const metrics=await command('Page.getLayoutMetrics');
  const size=metrics.cssContentSize;
  const result=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,
    clip:{x:0,y:0,width:size.width,height:size.height,scale:1}});
  await fs.writeFile(path.join(root,'docs/screenshots',name),Buffer.from(result.data,'base64'));
}
try{
  await command('Page.enable');await command('Runtime.enable');
  await command('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
  await navigate(base+'/');
  await capture('01-review-workspace.png');
  await evaluate('document.querySelector("[data-view=models]").click()');
  await waitFor('!document.querySelector("#models-view").hidden');
  await capture('02-model-lab.png');
  await evaluate('document.querySelector("[data-view=review]").click(); document.querySelector("#case-select").value="restricted-device"; document.querySelector("#case-select").dispatchEvent(new Event("change"))');
  await waitFor('document.querySelectorAll(".result-row").length===3 && document.querySelector("#case-tag").textContent==="Text warning"');
  const text=await evaluate('document.querySelector("#text-results").textContent');
  if(!text.includes('Account lock stated'))throw new Error('Missing text output');
  await evaluate('document.querySelector("#description").value=""; document.querySelector("#description").dispatchEvent(new Event("input"))');
  if(!await evaluate('document.querySelector("#review").disabled'))throw new Error('Stale predictions could be confirmed');
  await evaluate('document.querySelector("#case-select").value="surface-review"; document.querySelector("#case-select").dispatchEvent(new Event("change"))');
  await waitFor('document.querySelectorAll(".result-row").length===3');
  await evaluate('document.querySelector("[data-manual-field=screen_damage]").value="yes"; document.querySelector("[data-manual-field=screen_damage]").dispatchEvent(new Event("change",{bubbles:true}))');
  await evaluate('document.querySelector("#review").click()');
  if(!await evaluate('document.querySelector("#review-status").textContent.includes("unverified")'))throw new Error('Review semantics not visible');
  if(!await evaluate('document.querySelector("#review-status").textContent.includes("1 manual labels")'))throw new Error('Manual decision was not recorded');
  await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await navigate(base+'/');
  await capture('03-mobile-review.png');
  const overflow=await evaluate('document.documentElement.scrollWidth > window.innerWidth');
  if(overflow)throw new Error('Mobile layout overflows horizontally');
  if(errors.length)throw new Error('Browser errors: '+errors.join(', '));
  console.log('Captured 3 screenshots. Navigation, case switching, stale-result invalidation, review semantics and mobile layout passed.');
}finally{socket.close();}
