'use strict';
const preview=document.getElementById('demoFrame');
const display=document.getElementById('demoStatus');
addEventListener('message',e=>{
  if(e.origin!==location.origin||e.source!==preview?.contentWindow||!display)return;
  if(e.data?.type!=='openfids-demo-feed')return;
  const live=e.data.ok&&!e.data.stale;
  display.dataset.offline=String(!live);
  const count=Number.isFinite(e.data.count)?' · '+e.data.count+' flights':'';
  display.textContent=(live?'● NQA connected':e.data.count?'● Last received data':'● Feed unavailable')+count;
});
document.querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',async()=>{
  const original=button.textContent;
  const el=document.getElementById(button.dataset.copy);
  if(!el)return;
  try{await navigator.clipboard.writeText(el.textContent.trim());button.textContent='Copied ✓';}
  catch(e){const sel=getSelection(),range=document.createRange();range.selectNodeContents(el);sel.removeAllRanges();sel.addRange(range);button.textContent='Selected';}
  button.setAttribute('aria-live','polite');
  setTimeout(()=>button.textContent=original,2000);
}));


document.documentElement.classList.add("js");
const revealTargets = document.querySelectorAll(".hero-copy, .hero-art, .airports > *, .section-heading, .feature-grid article, .local-note, .demo-heading > *, .demo-shell, .disclaimer, .install > .kicker, .install > h2, .install > .section-copy, .installs article, .install-note, .footer > *");
revealTargets.forEach((target) => target.classList.add("scroll-reveal"));
if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      entry.target.classList.toggle("is-visible", entry.isIntersecting);
    });
  }, { threshold: 0.12 });
  revealTargets.forEach((target) => revealObserver.observe(target));
} else {
  revealTargets.forEach((target) => target.classList.add("is-visible"));
}
