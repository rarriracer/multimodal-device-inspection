const $=selector=>document.querySelector(selector);
const labels={screen_damage:'Display-Schäden genannt',cable_included:'Kabel vorhanden',account_lock:'Kontosperre genannt'};
const values={yes:'Ja',no:'Nein',unknown:'Unbekannt'};
const titles={
  'surface-review':['iPhone 13 · 128 GB · Graphit','Möglicher Widerspruch','Die Beschreibung verneint Kratzer. In der Bildansicht zeigt eine illustrative Markierung, wie ein möglicher Widerspruch geprüft wird.'],
  'accessory-check':['iPhone 13 Pro · 256 GB · Blau','Zubehör prüfen','Das Kabel wird im Text genannt. Die Bildansicht zeigt den getrennten Nachweis für Zubehör. Nicht sichtbare Gegenstände bleiben ungeprüft.'],
  'honest-uncertainty':['iPhone 12 · 128 GB · Silber','Angaben fehlen','Ohne eindeutige Angaben bleiben Zustand, Lieferumfang und Kontostatus unbekannt. Das Modell bestätigt keine Eigenschaften durch Schweigen.'],
  'stated-damage':['iPhone 12 · 64 GB · Graphit','Schaden beschrieben','Der Displaydefekt wird ausdrücklich beschrieben. Textangabe, Bildbefund und menschliche Prüfung bleiben getrennte Quellen.'],
  'multiple-devices':['Zwei iPhones · gemischte Ansichten','Gerätezuordnung prüfen','Bei mehreren Geräten muss jeder Befund dem passenden Gerät zugeordnet werden. Ein Listing-Label reicht dafür nicht aus.'],
  'restricted-device':['iPhone 13 · 128 GB · Graphit','Kontosperre genannt','Eine äußerlich unbeschädigte Oberfläche sagt nichts über den Kontostatus aus. Der Text nennt hier eine aktive Sperre.']
};
let cases=[],current=null,prediction=null,revision=0,reviewed=null,visionPrediction=null,visionRevision=0,activeView='review',listFilter='all';
const acknowledged=new Set();
const escapeHtml=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function applyTheme(dark){
  document.documentElement.classList.toggle('theme-dark',dark);
  $('#themeToggle').setAttribute('aria-pressed',String(dark));
  try{localStorage.setItem('dashboardTheme',dark?'dark':'light');}catch{}
}
$('#themeToggle').addEventListener('click',()=>applyTheme(!document.documentElement.classList.contains('theme-dark')));
try{applyTheme(localStorage.getItem('dashboardTheme')==='dark');}catch{applyTheme(false);}

function setView(name){
  if(!['board','review','image','models','about'].includes(name))name='review';
  activeView=name;
  for(const view of ['board','review','image','models','about'])$(`#${view}-view`).hidden=view!==name;
  document.querySelectorAll('nav [data-view]').forEach(button=>{
    button.classList.toggle('active',button.dataset.view===name);
    button.setAttribute('aria-current',button.dataset.view===name?'page':'false');
  });
  const headings={board:'Dashboard · Übersicht',review:'Labeling · Textmodell',image:'Bildmodell trainieren · Beispielansicht',models:'Modellübersicht',about:'Projektüberblick'};
  $('#detail-eyebrow').textContent=headings[name];
  $('#case-title').textContent=name==='board'?'Action Board':name==='models'?'Text- und Bildmodelle':name==='about'?'Multimodale Geräteprüfung':current?titles[current.id][0]:'Listing laden …';
  document.querySelector('.main-header > .actions').hidden=['board','models','about'].includes(name);
  history.replaceState(null,'',name==='review'?'/':`/?view=${name}`);
}
document.querySelectorAll('nav [data-view]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.view)));
function renderListings(){
  const filtered=cases.filter(item=>listFilter==='all'||(listFilter==='reviewed')===acknowledged.has(item.id));
  $('#listing-list').innerHTML=filtered.map(item=>`<button type="button" class="listing ${current?.id===item.id?'active':''}" data-case="${item.id}"><span class="listing-title">${titles[item.id][0]}</span><span class="listing-meta"><span class="pill ${item.id==='restricted-device'?'bad':item.id==='honest-uncertainty'?'warn':'info'}">${titles[item.id][1]}</span><span class="pill">Beispieldaten</span></span><span class="listing-footer"><span>Demo ${String(cases.indexOf(item)+1).padStart(3,'0')}</span><span>${acknowledged.has(item.id)?'✓ Geprüft':'○ Offen'}</span></span></button>`).join('');
  $('#empty-list').hidden=filtered.length>0;
  document.querySelectorAll('[data-case]').forEach(button=>button.onclick=()=>{$('#case-select').value=button.dataset.case;showCase(button.dataset.case);});
}
document.querySelectorAll('[data-list-filter]').forEach(button=>button.onclick=()=>{
  listFilter=button.dataset.listFilter;
  document.querySelectorAll('[data-list-filter]').forEach(item=>item.classList.toggle('active',item===button));
  renderListings();
});
function invalidateReview(clearLabels=true){
  reviewed=null;
  if(current)acknowledged.delete(current.id);
  if(clearLabels)document.querySelectorAll('[data-manual-field]').forEach(select=>select.value='');
  $('#review-status').textContent='Noch keine Prüfung gespeichert. Modellvorschläge sind unbestätigt.';
  $('#review').textContent='Prüfung speichern';
  renderListings();
}
function showCase(id){
  visionRevision++;
  visionPrediction=null;
  current=cases.find(item=>item.id===id);
  $('#case-image').src=current.image;
  $('#case-device').textContent='iPhone · lokale Demo';
  $('#case-tag').textContent=titles[id][1];
  $('#case-note').textContent=titles[id][2];
  $('#description').value=current.text.replace(/\. /g,'.\n\n');
  $('#overlays').innerHTML=current.findings.map(finding=>`<div class="overlay ${escapeHtml(finding.kind)}" style="left:${finding.box[0]}%;top:${finding.box[1]}%;width:${finding.box[2]}%;height:${finding.box[3]}%"><span>${finding.kind==='device'?'Handy / iPhone':finding.kind==='damage'?'Möglicher Schaden · Beispiel':'Zubehör · Beispiel'}</span></div>`).join('');
  $('#region-list').innerHTML=current.findings.map(finding=>`<div class="region-row"><i class="region-swatch ${finding.kind}"></i><span>${finding.kind==='device'?'Handy / iPhone':finding.kind==='damage'?'Möglicher Schaden':'Zubehör'} · Beispiel</span></div>`).join('');
  $('#vision-result').replaceChildren();$('#image-upload').value='';
  document.querySelectorAll('[data-region-view]').forEach(button=>{const active=button.dataset.regionView==='display';button.classList.toggle('on',active);button.setAttribute('aria-pressed',String(active));});
  invalidateReview();setView(activeView);analyse();
}
function highlightText(text,spans){
  const categories={screen_damage:'condition',cable_included:'accessory',account_lock:'technical'};
  let cursor=0,html='';
  for(const span of [...spans].sort((a,b)=>a.start-b.start)){
    if(span.start<cursor)continue;
    html+=escapeHtml(text.slice(cursor,span.start));
    html+=`<mark class="text-evidence text-evidence-${categories[span.field]}">${escapeHtml(text.slice(span.start,span.end))}</mark>`;
    cursor=span.end;
  }
  return html+escapeHtml(text.slice(cursor));
}
async function analyse(){
  const request=++revision;
  prediction=null;$('#analyse').disabled=true;$('#review').disabled=true;$('#export').disabled=true;
  $('#text-results').textContent='Lokales Textmodell wird ausgeführt …';
  try{
    const response=await fetch('/api/text',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:$('#description').value})});
    const result=await response.json();if(!response.ok)throw new Error(result.error);if(request!==revision)return;
    prediction=result;
    $('#text-results').innerHTML=Object.entries(result.fields).map(([field,p])=>`<div class="result-row"><div class="result-heading"><span>${labels[field]||escapeHtml(field)}</span><span class="model-confidence">Modell ${Math.round(p.score*100)} %</span></div><div class="choices">${Object.entries(values).map(([value,label])=>`<span class="choice ${value} ${p.value===value?'active':''}">${label}</span>`).join('')}</div></div>`).join('');
    $('#highlighted-description').innerHTML=highlightText($('#description').value,result.evidence);
    $('#evidence').innerHTML=result.evidence.length?result.evidence.map(e=>`<div class="text-evidence-row"><span><strong>${labels[e.field]}:</strong> „${escapeHtml(e.text)}“</span></div>`).join(''):'Keine passende Belegstelle erkannt.';
    invalidateReview();$('#review').disabled=false;$('#export').disabled=false;
  }catch(error){if(request===revision)$('#text-results').textContent=error.message;}
  finally{if(request===revision)$('#analyse').disabled=false;}
}
$('#analyse').addEventListener('click',analyse);
$('#description').addEventListener('input',()=>{
  revision++;prediction=null;invalidateReview();$('#review').disabled=true;$('#export').disabled=true;$('#analyse').disabled=false;
  $('#text-results').textContent='Text geändert. Bitte das Modell erneut ausführen.';
  $('#highlighted-description').textContent=$('#description').value;$('#evidence').replaceChildren();
});
$('#case-select').addEventListener('change',event=>showCase(event.target.value));
$('#show-overlays').addEventListener('change',event=>$('#overlays').hidden=!event.target.checked);
$('#review').addEventListener('click',()=>{
  if(!prediction)return;
  const manualLabels={};
  document.querySelectorAll('[data-manual-field]').forEach(select=>{if(select.value)manualLabels[select.dataset.manualField]={value:select.value,source:'human_review',physical_verification:false};});
  reviewed={at:new Date().toISOString(),labels:manualLabels,meaning:'Reviewer labels are separate from predictions; no physical verification is claimed.'};
  acknowledged.add(current.id);renderListings();
  $('#review-status').textContent=`Prüfung gespeichert · ${Object.keys(manualLabels).length} eigene Labels. Modellvorschläge bleiben unbestätigt.`;
  $('#review').textContent='Prüfung gespeichert ✓';
});
$('#export').addEventListener('click',()=>{
  if(!prediction)return;
  const payload={schema:'inspection-review/1',case_id:current.id,text:$('#description').value,predictions:prediction,
    visual_evidence_source:current.visual_source,uploaded_image_prediction:visionPrediction,review:reviewed,confirmed_facts:{},
    manually_selected_views:[...document.querySelectorAll('[data-region-view].on')].map(button=>button.dataset.regionView)};
  const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download='inspection-review.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
$('#image-upload').addEventListener('change',async event=>{
  const file=event.target.files[0];if(!file)return;
  if(file.size>8_000_000){$('#vision-result').textContent='Bitte ein Bild unter 8 MB auswählen.';return;}
  const target=$('#vision-result'),request=++visionRevision;visionPrediction=null;invalidateReview();
  target.textContent='Das trainierte Ansichtsmodell wird lokal ausgeführt …';
  try{
    const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});
    const response=await fetch('/api/vision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:encoded})});
    const result=await response.json();if(request!==visionRevision)return;if(!response.ok)throw new Error(result.error);
    visionPrediction=result;target.replaceChildren();
    const image=document.createElement('img'),objectUrl=URL.createObjectURL(file);image.src=objectUrl;image.alt='Dein lokal ausgewähltes Gerätefoto';image.onload=()=>URL.revokeObjectURL(objectUrl);target.append(image);
    const names={display:'Display',back:'Rückseite',camera:'Kamera'};
    const text=document.createElement('p');text.textContent=result.attributes.map(a=>`${names[a.label]}: ${a.score.toFixed(3)}`).join(' · ');target.append(text);
    const note=document.createElement('p');note.textContent='Echte Modellinferenz · unkalibrierte Scores · keine Schadensbewertung';target.append(note);
  }catch(error){if(request===visionRevision)target.textContent=error.message;}
});
function renderPhoneMaps(){
  const zone=(key,cls,label)=>`<button type="button" class="phone-zone ${cls} ${key==='display'?'on':''}" data-region-view="${key}" aria-pressed="${key==='display'}">${label}</button>`;
  const shell=back=>`<div class="phone-column"><div class="phone-caption">${back?'Rückseite':'Vorderseite'}</div><div class="phone-shell ${back?'back-shell':'front-shell'}">${zone(back?'back_top_left_corner':'top_left_corner','corner-tl','↖ Ecke')}${zone(back?'back_top':'top','edge-top','Oben')}${zone(back?'back_top_right_corner':'top_right_corner','corner-tr','Ecke ↗')}${zone(back?'back_left':'left','edge-left','Links')}${zone(back?'back':'display',back?'back-area':'screen',back?'Rückseite':'Display')}${zone(back?'back_right':'right','edge-right','Rechts')}${zone(back?'back_bottom_left_corner':'bottom_left_corner','corner-bl','↙ Ecke')}${zone(back?'back_bottom':'bottom','edge-bottom','Unten')}${zone(back?'back_bottom_right_corner':'bottom_right_corner','corner-br','Ecke ↘')}${back?zone('camera','camera-zone','Kamera'):''}</div></div>`;
  $('#views').innerHTML=`<div class="phone-maps">${shell(false)}${shell(true)}</div>`;
  document.querySelectorAll('[data-region-view]').forEach(button=>button.onclick=()=>{button.classList.toggle('on');button.setAttribute('aria-pressed',String(button.classList.contains('on')));invalidateReview(false);});
}
async function start(){
  try{
    renderPhoneMaps();
    $('#manual-labels').innerHTML=Object.entries(labels).map(([field,label])=>`<label>${label}<select data-manual-field="${field}" aria-label="Eigene Prüfung: ${label}"><option value="">Ungeprüft</option><option value="yes">Ja</option><option value="no">Nein</option><option value="unknown">Unbekannt</option></select></label>`).join('');
    $('#manual-labels').addEventListener('change',()=>invalidateReview(false));
    const response=await fetch('/api/examples');cases=await response.json();
    document.dispatchEvent(new Event('public-cases-ready'));
    $('#case-select').innerHTML=cases.map((item,i)=>`<option value="${item.id}">Demo ${i+1} · ${titles[item.id][1]}</option>`).join('');
    activeView=new URLSearchParams(location.search).get('view')||'review';showCase(cases[0].id);
  }catch(error){$('#text-results').textContent='Bitte den lokalen Python-Demoserver starten.';}
}
start();
