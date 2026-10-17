window.RTF={"standard_le350": [[0, 150000, 2.0], [150000, 200000, 3.35], [200000, 350000, 3.9]], "standard_gt350": [[0, 150000, 2.9], [150000, 200000, 4.25], [200000, 550000, 4.8], [550000, 850000, 5.3], [850000, 1000000, 5.8], [1000000, null, 6.05]], "reduced_le350": [[0, 150000, 0.5], [150000, 350000, 1.25]], "reduced_gt350": [[0, 150000, 1.4], [150000, 550000, 2.15], [550000, 850000, 2.65], [850000, 1000000, 3.15], [1000000, null, 3.4]], "gpf": [[1000000, 2000000, 1.0], [2000000, 2500000, 2.0], [2500000, 3000000, 2.5], [3000000, 3500000, 3.0], [3500000, null, 3.5]], "tests": [[325000, "standard", 1910.0], [280000, "reduced", 475.0]]};
(function(){
  // Town finder: search + chips
  document.querySelectorAll('.finder').forEach(function(f){
    var q=f.querySelector('#q'),cards=[].slice.call(f.querySelectorAll('.tcard')),cnt=f.querySelector('#count'),filt={f:'all',v:''};
    function run(){var s=(q.value||'').trim().toLowerCase(),n=0;
      cards.forEach(function(c){var ok=(!s||c.dataset.name.indexOf(s)>-1)&&(filt.f==='all'||c.dataset[filt.f]===filt.v);c.style.display=ok?'':'none';if(ok)n++;});
      if(cnt)cnt.textContent='Showing '+n+' of '+cards.length+' towns';}
    q&&q.addEventListener('input',run);
    f.querySelectorAll('.chip').forEach(function(b){b.addEventListener('click',function(){f.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on')});b.classList.add('on');filt={f:b.dataset.f,v:b.dataset.v};run();});});
    run();
  });
  // Transfer fee calculator (mirrors build.py rtf()/gpf())
  var p=document.getElementById('cprice');
  if(p&&window.RTF){var R=window.RTF,red=document.getElementById('cred'),cl=document.getElementById('cclass');
    function tiers(x,t){var f=0;t.forEach(function(r){if(x>r[0]){var top=r[1]===null?x:Math.min(x,r[1]);f+=(top-r[0])/500*r[2];}});return f;}
    function fmt(n){return '$'+Math.round(n).toLocaleString('en-US');}
    function calc(){var x=parseFloat((p.value||'').replace(/[^0-9.]/g,''))||0;
      var k=(red.checked?'reduced':'standard')+(x<=350000?'_le350':'_gt350');var r=tiers(x,R[k]);var g=0;
      if(cl.value==='res')R.gpf.forEach(function(t){if(x>t[0]&&(t[1]===null||x<=t[1]))g=x*t[2]/100;});
      document.getElementById('o-rtf').textContent=fmt(r);document.getElementById('o-gpf').textContent=g?fmt(g):'$0 (n/a)';document.getElementById('o-tot').textContent=fmt(r+g);}
    [p,red,cl].forEach(function(el){el.addEventListener('input',calc);el.addEventListener('change',calc);});calc();}
  // Checklist persistence
  var ck=document.querySelectorAll('.checks input');
  if(ck.length){var key='sjsg-checklist';var st={};try{st=JSON.parse(localStorage.getItem(key)||'{}')}catch(e){}
    ck.forEach(function(c,i){c.checked=!!st[i];c.addEventListener('change',function(){st[i]=c.checked;try{localStorage.setItem(key,JSON.stringify(st))}catch(e){}});});}
})();
