// Public Action Board. All amounts and non-text facts are authored UI fixtures.
const boardFixtures={
  'surface-review':{box:'yes',battery:89,cost:189,quote:235,review:true,missing:false},
  'accessory-check':{box:'yes',battery:92,cost:279,quote:310,review:false,missing:true},
  'honest-uncertainty':{box:'unknown',battery:null,cost:159,quote:190,review:false,missing:true},
  'stated-damage':{box:'no',battery:81,cost:119,quote:145,review:false,missing:false},
  'multiple-devices':{box:'unknown',battery:null,cost:249,quote:null,review:true,missing:true},
  'restricted-device':{box:'no',battery:87,cost:169,quote:210,review:true,missing:false}
};
let boardResults=new Map(),boardFilter='all',boardRequest=0;
const euro=value=>value===null?'–':new Intl.NumberFormat('de-DE',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(value);
function boardFact(value,negativeIsRisk=false){
  const tone=value==='unknown'?'warn':value==='yes'&&negativeIsRisk?'bad':value==='no'&&!negativeIsRisk?'warn':'ok';
  const text=value==='unknown'?'?':value==='yes'?'✓':'—';
  return `<span class="pill ${tone}" title="${values[value]||'Unbekannt'}">${text}</span>`;
}
function renderBoard(){
  if(!cases.length)return;
  const query=$('#board-search').value.toLowerCase().trim();
  const rows=cases.filter((item,index)=>{
    const fixture=boardFixtures[item.id];
    return (boardFilter==='all'||(boardFilter==='review'?fixture.review:fixture.missing))&&
      `${titles[item.id][0]} demo ${index+1} ${titles[item.id][1]}`.toLowerCase().includes(query);
  });
  if($('#board-sort').value==='name')rows.sort((a,b)=>titles[a.id][0].localeCompare(titles[b.id][0]));
  $('#board-rows').innerHTML=rows.map(item=>{
    const fixture=boardFixtures[item.id],result=boardResults.get(item.id),index=cases.indexOf(item)+1;
    const cable=result?.fields.cable_included.value||'unknown';
    const damage=result?.fields.screen_damage.value||'unknown';
    const difference=fixture.quote===null?null:fixture.quote-fixture.cost;
    return `<tr data-board-case="${item.id}"><td><div class="collective-device"><i class="collective-device-icon"></i><strong>${titles[item.id][0]}</strong></div><span class="board-demo-id">Demo ${String(index).padStart(3,'0')} · Beispieldaten</span></td><td>${boardFact(fixture.box)}</td><td>${boardFact(cable)}</td><td><span class="pill ${fixture.battery?'ok':'warn'}">${fixture.battery?fixture.battery+' %':'?'}</span></td><td>${boardFact(damage,true)}</td><td class="board-money">${euro(fixture.cost)}</td><td><strong>${euro(fixture.quote)}</strong><small class="board-demo-id">Fiktiver Vergleich</small></td><td><span class="pill ${difference===null?'warn':'ok'}">${euro(difference)}</span></td><td><span class="pill ${fixture.review?'warn':fixture.missing?'info':'ok'}">${fixture.review?'Prüfen':fixture.missing?'Angaben offen':'Text ausgewertet'}</span></td><td><div class="board-model-headings model-status-row"><span class="model-indicator ${result?'done':''}" title="${result?'Textmodell tatsächlich ausgeführt':'Textmodell offen'}">${result?'✓':'○'}</span><span class="model-indicator" title="Merkmalsmodell nicht ausgeführt">○</span><span class="model-indicator" title="Schadensmodell nicht ausgeführt">○</span></div></td><td><button class="btn" data-open-board-case="${item.id}">Prüfen ↗</button></td></tr>`;
  }).join('')||'<tr><td colspan="11" class="collective-empty">Keine passenden Beispielangebote.</td></tr>';
  $('#board-count').textContent=`${rows.length} Angebote · Seite 1 / 1`;
  const metrics=[['Listings im Action Board',cases.length],['Textprüfung vorhanden',boardResults.size],['Textprüfung offen',cases.length-boardResults.size],['Zur Prüfung markiert',cases.filter(item=>boardFixtures[item.id].review).length],['Angaben offen',cases.filter(item=>boardFixtures[item.id].missing).length]];
  $('#board-summary').innerHTML=metrics.map(([label,total])=>`<tr><th scope="row">${label}</th><td>${total}</td><td>0</td><td>0</td><td>0</td><td>0</td><td>${total}</td></tr>`).join('');
  document.querySelectorAll('[data-open-board-case]').forEach(button=>button.onclick=()=>{
    $('#case-select').value=button.dataset.openBoardCase;showCase(button.dataset.openBoardCase);setView('review');
  });
}
async function analyseBoard(){
  if(!cases.length)return;
  const request=++boardRequest;
  $('#board-analyse').disabled=true;$('#board-model-status').textContent='Textauswertung läuft …';
  try{
    const results=await Promise.all(cases.map(async item=>{
      const response=await fetch('/api/text',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:item.text})});
      const result=await response.json();if(!response.ok)throw new Error(result.error);return [item.id,result];
    }));
    if(request!==boardRequest)return;
    boardResults=new Map(results);renderBoard();$('#board-model-status').textContent=`Text · ${results.length} / ${cases.length} ausgewertet`;
    $('#board-feedback').textContent='Textfelder wurden mit dem öffentlichen Modell ausgewertet. Zubehör-, Akku-, Preis- und Prüfbedarfsangaben sind erfundene UI-Beispiele. Die Bildmodelle wurden für diese Übersicht nicht ausgeführt.';
  }catch(error){if(request===boardRequest){$('#board-model-status').textContent='Textauswertung fehlgeschlagen';$('#board-feedback').textContent=error.message;}}
  finally{if(request===boardRequest)$('#board-analyse').disabled=false;}
}
$('#board-analyse').addEventListener('click',analyseBoard);
$('#board-search').addEventListener('input',renderBoard);
$('#board-sort').addEventListener('change',renderBoard);
document.querySelectorAll('[data-board-filter]').forEach(button=>button.onclick=()=>{
  boardFilter=button.dataset.boardFilter;
  document.querySelectorAll('[data-board-filter]').forEach(tab=>tab.setAttribute('aria-selected',String(tab===button)));
  renderBoard();
});
$('#board-reset').addEventListener('click',()=>{
  $('#board-search').value='';$('#board-sort').value='id';document.querySelector('[data-board-filter=all]').click();analyseBoard();
});
document.addEventListener('public-cases-ready',()=>{renderBoard();analyseBoard();});
if(cases.length){renderBoard();analyseBoard();}
