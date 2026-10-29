const preview=document.getElementById('demoFrame');
const display=document.getElementById('demoStatus');
addEventListener('message',e=>{
  if(e.origin!==location.origin||e.source!==preview.contentWindow)return;
  if(e.data?.type!=='openfids-demo-feed')return;
  const live=e.data.ok&&!e.data.stale;
  display.dataset.offline=String(!live);
  const count=Number.isFinite(e.data.count)?' · '+e.data.count+' flights':'';
  display.textContent=(live?'● NQA connected':'● NQA unavailable')+count;
});
document.querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',async()=>{
  const original=button.textContent;
  const el=document.getElementById(button.dataset.copy);
  try{await navigator.clipboard.writeText(el.textContent.trim());button.textContent='Copied ✓';}
  catch(e){const sel=getSelection(),range=document.createRange();range.selectNodeContents(el);sel.removeAllRanges();sel.addRange(range);button.textContent='Select text';}
  setTimeout(()=>button.textContent=original,2000);
}));
