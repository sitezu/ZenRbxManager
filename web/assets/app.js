/* ZenRbxManager: real account state, no prototype demo records. */
'use strict';
const $ = id => document.getElementById(id);
let appState = {accounts:[], settings:{}};
let selectedName = null, editName = null, hiddenNames = false, filter = 'all', noteTimer = null, toastTimer = null, dragged = null;
const palette = {
  indigo:['139 137 255','99 102 241','79 70 229'], cyan:['34 211 238','6 182 212','8 145 178'],
  emerald:['52 211 153','16 185 129','5 150 105'], amber:['251 191 36','245 158 11','217 119 6'],
  rose:['251 113 133','244 63 94','225 29 72'], violet:['165 180 252','99 102 241','79 70 229']
};
function toast(text, bad=false) {
 const el=$('toast'); el.textContent=text; el.classList.remove('hidden');
 el.style.borderColor=bad?'#f43f5e':''; clearTimeout(toastTimer);
 toastTimer=setTimeout(()=>el.classList.add('hidden'),6000);
}
async function api(kind, body={}) {
 const response=await fetch('/api/'+kind,{method:'POST',headers:{'Content-Type':'application/json','X-Zen-Token':ZEN_TOKEN},body:JSON.stringify(body)});
 const result=await response.json(); if(!response.ok) throw Error(result.error||'Request failed'); return result;
}
async function execute(kind, body={}, callback) {
 try { const result=await api(kind,body); if(result.state) updateState(result.state);
   if(result.message) toast(result.message); if(callback) await callback(result); return result;
 } catch(e) { toast(e.message,true); return null; }
}
function updateState(state) {
 const checked=new Set([...document.querySelectorAll('.row-checkbox:checked')].map(n=>n.closest('.account-row').dataset.username));
 appState=state;
 const list=$('accountList'); list.replaceChildren();
 for(const item of state.accounts) {
  const row=document.createElement('div'); row.draggable=true;
  row.className='account-row account-grid bg-panel border border-borderSubtle hover:border-th-400/50 p-2 rounded-xl group shrink-0';
  row.dataset.username=item.username; row.dataset.alias=item.alias; row.dataset.status=item.status;
  const select=document.createElement('div'); select.className='flex justify-center';
  const checkbox=document.createElement('input'); checkbox.type='checkbox';checkbox.className='row-checkbox';checkbox.checked=checked.has(item.username);
  checkbox.setAttribute('aria-label','Select '+item.username); select.append(checkbox); row.append(select);
  const name=document.createElement('div');name.className='text-xs font-bold text-slate-100 truncate cursor-pointer account-name';
  name.textContent=hiddenNames?'••••••••':item.username; name.title='Select account'; name.addEventListener('click',()=>selectAccount(item.username));row.append(name);
  const status=document.createElement('div');status.className='text-[10px] font-semibold capitalize truncate cursor-pointer bg-inputBg rounded-full p-1';
  status.textContent='● '+(item.status==='ingame'?'In-Game':item.status);status.title='Live presence when Roblox responds; Away is manual';
  status.style.color={online:'#34d399',ingame:'#818cfc',away:'#fbbf24',offline:'#94a3b8',unknown:'#64748b'}[item.status]||'#64748b';
  status.addEventListener('click',()=>selectAccount(item.username));row.append(status);
  const alias=document.createElement('div');alias.className='text-[10px] font-semibold text-slate-400 bg-inputBg px-2 py-0.5 rounded border border-borderSubtle text-center truncate cursor-pointer';alias.textContent=item.alias||'—';alias.addEventListener('click',()=>selectAccount(item.username));row.append(alias);
  const note=document.createElement('div');note.className='text-[11px] text-slate-500 truncate cursor-pointer';note.textContent=item.note;note.addEventListener('click',()=>selectAccount(item.username));row.append(note);
  const actions=document.createElement('div');actions.className='flex justify-end gap-1';
  for(const [icon,title,cb] of [['fa-key','Copy Cookie',()=>copyAccountCookie(item.username)],['fa-pen','Edit',()=>openEditModal(item.username)],['fa-trash-can','Delete',()=>deleteAccount(item.username)]]) {
    const btn=document.createElement('button');btn.className='text-slate-400 hover:text-th-400 p-1';btn.title=title;btn.setAttribute('aria-label',title+' '+item.username);
    const i=document.createElement('i');i.className='fa-solid '+icon;btn.append(i);btn.addEventListener('click',cb);actions.append(btn);
  }row.append(actions);list.append(row);
 }
 if(!state.accounts.length){const empty=document.createElement('div');empty.id='emptyStateNotice';empty.className='h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 space-y-2';empty.textContent='No accounts added yet. Click “Add New Account” to get started.';list.append(empty);}
 if(selectedName&&!state.accounts.some(x=>x.username===selectedName)){selectedName=null;$('descInput').value='';updateCharCount();}
 applyFilter();applySettings();
}
function applyFilter(){const search=$('accountSearchInput').value.trim().toLowerCase();let visible=0;
 document.querySelectorAll('.account-row').forEach(row=>{const yes=(row.dataset.username.toLowerCase().includes(search)||row.dataset.alias.toLowerCase().includes(search))&&(filter==='all'||row.dataset.status===filter);row.style.display=yes?'grid':'none';if(yes)visible++;});
 $('masterCheckbox').checked=false;
}
function filterAccounts(){applyFilter()}
function setStatusFilter(status){filter=status;for(const s of ['all','online','ingame','away','offline']){
 const btn=$('filter-'+s);btn.classList.toggle('bg-th-500',s===status);btn.classList.toggle('text-white',s===status);btn.classList.toggle('bg-inputBg',s!==status);btn.classList.toggle('text-slate-400',s!==status);}
 applyFilter();}
function toggleSelectAll(){const checked=$('masterCheckbox').checked;document.querySelectorAll('.account-row').forEach(row=>{if(row.style.display!=='none')row.querySelector('.row-checkbox').checked=checked;});}
function selectedAccounts(){const checked=[...document.querySelectorAll('.row-checkbox:checked')].map(el=>el.closest('.account-row').dataset.username);
 return checked.length?checked:(selectedName?[selectedName]:[]);}
function selectAccount(name){clearTimeout(noteTimer);selectedName=name;const account=appState.accounts.find(x=>x.username===name);if(!account)return;
 $('descInput').value=account.note;updateCharCount();document.querySelectorAll('.account-row').forEach(row=>row.style.borderColor=row.dataset.username===name?'rgb(var(--th-400))':'');toast('Selected '+name);}
function toggleNames(){hiddenNames=!hiddenNames;$('eyeIcon').classList.toggle('fa-eye',!hiddenNames);$('eyeIcon').classList.toggle('fa-eye-slash',hiddenNames);for(const el of document.querySelectorAll('.account-name'))el.textContent=hiddenNames?'••••••••':el.closest('.account-row').dataset.username;}
function updateCharCount(){$('charCounter').textContent=$('descInput').value.length+' / 250';}
function queueNoteSave(){if(!selectedName)return;clearTimeout(noteTimer);const name=selectedName,note=$('descInput').value;noteTimer=setTimeout(()=>execute('note',{username:name,note}),650);}
function insertTemplate(text){$('descInput').value=text;updateCharCount();queueNoteSave();}
function showModal(id){$(id).classList.remove('hidden','opacity-0');$(id).classList.add('flex');}
function hideModal(id){$(id).classList.remove('flex');$(id).classList.add('hidden');}
function openAddAccountModal(){showModal('addAccountModal');}
function closeAddAccountModal(){hideModal('addAccountModal');}
function openPlaceModal(){showModal('placeModal');}
function closePlaceModal(){hideModal('placeModal');}
function openSettingsModal(){showModal('settingsModal');}
function closeSettingsModal(){hideModal('settingsModal');}
function openEditModal(name){const account=appState.accounts.find(x=>x.username===name);if(!account)return;
 editName=name;$('editUsername').value=account.username;$('editAlias').value=account.alias;$('editDesc').value=account.note;$('editAway').checked=account.status==='away';showModal('editModal');}
function closeEditModal(){hideModal('editModal');}
function switchAddTab(tab){$('addWebsiteSection').classList.toggle('hidden',tab!=='website');$('addCookieSection').classList.toggle('hidden',tab!=='cookie');$('tabWebsiteBtn').style.color=tab==='website'?'rgb(var(--th-400))':'';$('tabCookieBtn').style.color=tab==='cookie'?'rgb(var(--th-400))':'';}
async function confirmCookieImport(){const cookie=$('cookieInput').value.trim();if(!cookie)return toast('Paste a Roblox security cookie.',true);
 const result=await execute('cookie_import',{cookie});if(result){$('cookieInput').value='';$('cookieUsernameInput').value='';closeAddAccountModal();}}
async function confirmWebsiteLogin(){closeAddAccountModal();toast('Sign in to Roblox in the browser window, then close it when finished.');await execute('browser_login');}
async function saveEditedAccount(){const result=await execute('edit',{username:editName,new_username:$('editUsername').value,alias:$('editAlias').value,note:$('editDesc').value,away:$('editAway').checked});
 if(result){if(selectedName===editName){$('descInput').value=$('editDesc').value;updateCharCount();}closeEditModal();}}
async function deleteAccount(name){if(confirm('Remove '+name+' from this computer?'))await execute('delete',{username:name});}
async function copyAccountCookie(name){if(!confirm('Copy the login cookie for '+name+'? Anyone with it can access this Roblox account.'))return;
 const result=await execute('cookie_copy',{username:name});if(!result)return;
 try{await navigator.clipboard.writeText(result.cookie);toast('Cookie copied. Keep it private.');}
 catch(e){toast('Clipboard permission denied. No cookie was shown.',true);}}
async function launch(names,place='',job=''){if(!names.length)return toast('Select an account first.',true);
 const result=await execute('launch',{names,place,job});if(result?.results){const failed=result.results.filter(x=>!x.ok);if(failed.length)toast(failed.map(x=>x.username+': '+x.message).join(' | '),true);}}
function batchLaunchSelected(){launch(selectedAccounts());}
function launchMainApp(){launch(selectedAccounts());}
function confirmJoinPlace(){const place=$('modalPlaceId').value.trim(),job=$('modalJobId').value.trim();if(!place)return toast('Place ID is required.',true);
 closePlaceModal();launch(selectedAccounts(),place,job);}
function applyTheme(name){const colors=palette[name]||palette.indigo;colors.forEach((c,i)=>document.documentElement.style.setProperty('--th-'+(400+i*100),c));
 document.querySelectorAll('.theme-btn').forEach(btn=>{btn.style.outline=btn.dataset.theme===name?'2px solid white':'none';});}
function setTheme(name){applyTheme(name);execute('settings',{key:'theme',value:name});}
function applySettings(){const cfg=appState.settings;applyTheme(cfg.theme);$('prefBloxstrap').checked=Boolean(cfg.bloxstrap);$('prefStartup').checked=Boolean(cfg.startup);$('prefBrowser').value=cfg.browser||'edge';$('prefDelay').value=cfg.delay??0.5;}
async function runUtility(type){if(type==='export'){
 const result=await execute('export');if(result){const blob=new Blob([JSON.stringify(result.config,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=result.filename;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),5000);toast('Config downloaded without account cookies.');}
 }else if(type==='import'){$('configFile').click();}else if(type==='cookies'){
 if(confirm('Remove old temporary login browser profiles? Saved account cookies will be kept.'))await execute('clear_cache');}
 closeSettingsModal();}
async function windowAction(action){await execute('window',{action});}
const list=$('accountList');
list.addEventListener('dragstart',e=>{dragged=e.target.closest('.account-row');if(dragged)e.dataTransfer.effectAllowed='move';});
list.addEventListener('dragover',e=>{if(!dragged)return;e.preventDefault();const row=e.target.closest('.account-row');if(row&&row!==dragged){const bounds=row.getBoundingClientRect();list.insertBefore(dragged,e.clientY<bounds.top+bounds.height/2?row:row.nextSibling);}});
list.addEventListener('drop',async e=>{if(!dragged)return;e.preventDefault();dragged=null;await execute('order',{names:[...list.querySelectorAll('.account-row')].map(x=>x.dataset.username)});});
list.addEventListener('dragend',()=>{dragged=null;});
for(const id of ['placeModal','editModal','addAccountModal','settingsModal'])$(id).addEventListener('click',e=>{if(e.target===$(id))hideModal(id);});
$('configFile').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;
 try{if(file.size>32768)throw Error('Config file is too large.');const config=JSON.parse(await file.text());await execute('import',{config});}catch(err){toast(err.message,true);}e.target.value='';});
for(const [id,key] of [['prefBloxstrap','bloxstrap'],['prefStartup','startup'],['prefBrowser','browser'],['prefDelay','delay']])$(id).addEventListener('change',async e=>{
 const value=key==='delay'?Number(e.target.value):key==='browser'?e.target.value:e.target.checked;
 const r=await execute('settings',{key,value});if(!r)applySettings();});
window.addEventListener('beforeunload',()=>{clearTimeout(noteTimer);});
execute('state');
setInterval(async()=>{try{const state=await api('state');if(!document.querySelector('.row-checkbox:checked')&&!dragged)updateState(state);}catch(e){}},45000);
