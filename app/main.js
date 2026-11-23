const $ = selector => document.querySelector(selector);
const labels = {screen_damage:'Screen damage stated', cable_included:'Cable included', account_lock:'Account lock stated'};
let cases = [], current = null, prediction = null, revision = 0, reviewed = null;
let visionPrediction = null, visionRevision = 0;
const escapeHtml = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function setView(name) {
  if (!['review','models','about'].includes(name)) name='review';
  for (const view of ['review','models','about']) $(`#${view}-view`).hidden = view !== name;
  document.querySelectorAll('[data-view]').forEach(button => {
    button.classList.toggle('active', button.dataset.view===name);
    button.setAttribute('aria-current', button.dataset.view===name?'page':'false');
    button.setAttribute('aria-label', button.textContent.trim());
  });
  history.replaceState(null, '', name==='review'?'/':`/?view=${name}`);
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click',()=>setView(button.dataset.view)));

function invalidateReview(clearLabels=true) {
  reviewed = null;
  if(clearLabels)document.querySelectorAll('[data-manual-field]').forEach(select=>select.value='');
  $('#review-status').textContent='No inspection has been confirmed. Example overlays are illustrative.';
  $('#review').textContent='Mark as reviewed ↗';
}
function showCase(id) {
  visionRevision++;
  visionPrediction=null;
  current = cases.find(item=>item.id===id);
  $('#case-image').src=current.image;
  $('#case-title').textContent=current.title;
  $('#case-device').textContent=current.device;
  $('#case-tag').textContent=current.tag;
  $('#case-note').textContent=current.note;
  $('#description').value=current.text;
  $('#overlays').innerHTML=current.findings.map(finding=>`<div class="overlay ${escapeHtml(finding.kind)}" style="left:${finding.box[0]}%;top:${finding.box[1]}%;width:${finding.box[2]}%;height:${finding.box[3]}%"><span>${escapeHtml(finding.label)}</span></div>`).join('');
  $('#vision-result').replaceChildren();
  $('#image-upload').value='';
  invalidateReview();
  analyse();
}

async function analyse() {
  const request=++revision;
  prediction=null;
  $('#analyse').disabled=true;
  $('#review').disabled=true;
  $('#export').disabled=true;
  $('#text-results').textContent='Running local classifier…';
  try {
    const response=await fetch('/api/text',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:$('#description').value})});
    const result=await response.json();
    if (!response.ok) throw new Error(result.error);
    if (request!==revision) return;
    prediction=result;
    $('#text-results').innerHTML=Object.entries(result.fields).map(([field,p])=>`<div class="result-row"><span>${labels[field]||escapeHtml(field)}</span><span class="result-value ${p.value}">${escapeHtml(p.value)}</span><span class="score-track"><i style="width:${Math.round(p.score*100)}%"></i></span><span class="score">${p.score.toFixed(2)}</span></div>`).join('');
    $('#evidence').innerHTML=result.evidence.length?result.evidence.map(e=>`<span class="evidence-chip">${escapeHtml(e.text)}</span>`).join(''):'<span class="evidence-chip">No supported phrase match</span>';
    invalidateReview();
    $('#review').disabled=false;
    $('#export').disabled=false;
  } catch(error) {
    if(request===revision) $('#text-results').textContent=error.message;
  } finally {
    if(request===revision) $('#analyse').disabled=false;
  }
}
$('#analyse').addEventListener('click',analyse);
$('#description').addEventListener('input',()=>{
  revision++;
  prediction=null;
  invalidateReview();
  $('#review').disabled=true;
  $('#export').disabled=true;
  $('#analyse').disabled=false;
  $('#text-results').textContent='Text changed. Analyse again to refresh the suggestions.';
  $('#evidence').replaceChildren();
});
$('#case-select').addEventListener('change',event=>showCase(event.target.value));
$('#show-overlays').addEventListener('change',event=>$('#overlays').hidden=!event.target.checked);
$('#review').addEventListener('click',()=>{
  if(!prediction)return;
  const manualLabels={};
  document.querySelectorAll('[data-manual-field]').forEach(select=>{
    if(select.value)manualLabels[select.dataset.manualField]={value:select.value,source:'human_review',physical_verification:false};
  });
  reviewed={at:new Date().toISOString(),labels:manualLabels,meaning:'Reviewer labels are separate from predictions; no physical verification is claimed.'};
  $('#review-status').textContent=`Review acknowledged. ${Object.keys(manualLabels).length} manual labels recorded. Model predictions remain unverified.`;
  $('#review').textContent='Review acknowledged ✓';
});
$('#export').addEventListener('click',()=>{
  if(!prediction)return;
  const payload={schema:'inspection-review/1',case_id:current.id,text:$('#description').value,predictions:prediction,
    visual_evidence_source:current.visual_source,uploaded_image_prediction:visionPrediction,review:reviewed,confirmed_facts:{}};
  const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download='inspection-review.json';link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});
$('#image-upload').addEventListener('change',async event=>{
  const file=event.target.files[0];
  if(!file)return;
  if(file.size>8_000_000){$('#vision-result').textContent='Choose an image smaller than 8 MB.';return;}
  const target=$('#vision-result'), request=++visionRevision;
  visionPrediction=null;
  invalidateReview();
  target.textContent='Running the trained view model locally…';
  try {
    const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});
    const response=await fetch('/api/vision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:encoded})});
    const result=await response.json();
    if(request!==visionRevision)return;
    if(!response.ok)throw new Error(result.error);
    visionPrediction=result;
    target.replaceChildren();
    const image=document.createElement('img'),objectUrl=URL.createObjectURL(file);image.src=objectUrl;image.alt='Your locally selected device photo';image.onload=()=>URL.revokeObjectURL(objectUrl);target.append(image);
    const text=document.createElement('p');text.textContent=result.attributes.map(a=>`${a.label}: ${a.score.toFixed(3)}`).join(' · ');target.append(text);
    const note=document.createElement('p');note.textContent='Actual model scores. Uncalibrated; not a damage assessment.';target.append(note);
  } catch(error) {if(request===visionRevision)target.textContent=error.message;}
});

async function start() {
  try {
    $('#manual-labels').innerHTML=Object.entries(labels).map(([field,label])=>`<label>${label}<select data-manual-field="${field}" aria-label="Reviewer decision: ${label}"><option value="">Unreviewed</option><option value="yes">Yes</option><option value="no">No</option><option value="unknown">Unknown</option></select></label>`).join('');
    $('#manual-labels').addEventListener('change',()=>invalidateReview(false));
    const response=await fetch('/api/examples');
    cases=await response.json();
    $('#case-select').innerHTML=cases.map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.title)}</option>`).join('');
    showCase(cases[0].id);
    setView(new URLSearchParams(location.search).get('view')||'review');
  } catch(error){$('#text-results').textContent='Start the Python demo server to load the examples.';}
}
start();
