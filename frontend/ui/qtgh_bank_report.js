/* Bank allocations from locked settlements; reconciliation is separate from posting. */
window.openBankReport=async function(){
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const fmt=v=>Number(v||0).toLocaleString('vi-VN');
 const statuses={CHUA_DOI_CHIEU:'Chưa đối chiếu',DA_KHOP:'Đã khớp',CHENH_LECH:'Chênh lệch'};
 const parts=new Intl.DateTimeFormat('en',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
 const part=k=>parts.find(p=>p.type===k).value;const today=part('year')+'-'+part('month')+'-'+part('day');
 let dlg=document.getElementById('bankReportDialog');if(dlg)dlg.remove();
 dlg=document.createElement('dialog');dlg.id='bankReportDialog';dlg.style.cssText='width:96vw;max-width:1600px;max-height:94vh';
 dlg.innerHTML=`<style>#bankReportDialog input,#bankReportDialog select{padding:7px;max-width:200px}#bankReportDialog label{display:grid;gap:4px}#bankReportDialog table{border-collapse:collapse;width:100%;font-size:12px}#bankReportDialog th,#bankReportDialog td{border:1px solid #cbd5e1;padding:7px;vertical-align:top}#bankReportDialog th{background:#eaf1f6}#bankReportDialog .money{text-align:right;white-space:nowrap}#bankReportDialog .stats{background:#ecf5f6;padding:12px;margin:12px 0}#bankReportDialog .warning{color:#92400e}</style>
 <h2>Mã Ngân Hàng</h2><div style="display:flex;gap:10px;flex-wrap:wrap">
 <label>Ngày quyết toán từ<input id="brFrom" type="date" value="${today}"></label><label>Đến ngày<input id="brTo" type="date" value="${today}"></label>
 <label>Ngân hàng / Tài khoản nhận<select id="brBank"><option value="">Tất cả</option></select></label>
 <label>NV giao hàng<input id="brStaff" placeholder="Mã hoặc tên NVGH"></label>
 <label>Khách hàng<input id="brCustomer" placeholder="Mã hoặc tên KH"></label><label>Mã lô<input id="brLot"></label>
 <label>Mã giao dịch / Đơn / Phiếu QT<input id="brTxn"></label><label>Đối chiếu<select id="brStatus"><option value="">Tất cả</option>${Object.entries(statuses).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label>
 <button id="brLoad">Tra cứu</button><button id="brPrint" disabled>In / Lưu PDF</button><button id="brExport" disabled>Xuất Excel</button><button id="brClose">Đóng</button></div>
 <p>Chỉ gồm chuyển khoản trên đơn đã chốt quyết toán. Ngày quyết toán và ngày chuyển tiền trên sao kê được thể hiện riêng.</p>
 <p id="brError" style="color:#b91c1c"></p><div id="brBody" style="overflow:auto"></div>`;
 document.body.append(dlg);dlg.showModal();const el=id=>dlg.querySelector('#'+id);
 el('brClose').onclick=()=>dlg.close();
 const root='/api/qtgh-stable/ui04/bank-report';let data=null,loadedParams='',canEdit=false;const pending=new Map();
 const params=()=>new URLSearchParams({date_from:el('brFrom').value,date_to:el('brTo').value,bank_key:el('brBank').value,
 staff:el('brStaff').value.trim(),customer:el('brCustomer').value.trim(),lot:el('brLot').value.trim(),txn:el('brTxn').value.trim(),status:el('brStatus').value}).toString();
 const cols=['STT','Ngày quyết toán','Ngày trên sao kê','Mã KH','Tên KH','Đơn nguồn','Mã lô / Phiếu QT','NVGH','Ngân hàng nhận / Tài khoản','Mã giao dịch','Số tiền CK','Đối chiếu','Ghi chú'];
 function content(edit){
  const f=data.filters;const summary=[f.date_from?'Từ '+f.date_from:'',f.date_to?'Đến '+f.date_to:'',f.bank_key?'TK: '+(data.banks.find(b=>b.key===f.bank_key)?.label||f.bank_key):'',f.staff?'NVGH: '+f.staff:'',f.customer?'KH: '+f.customer:'',f.lot?'Lô: '+f.lot:'',f.txn?'Tìm: '+f.txn:'',f.status?statuses[f.status]:''].filter(Boolean).map(esc).join(' · ');
  return `<h2>CTY CP Vĩnh Giang</h2><h1>Mã Ngân Hàng</h1><p>${summary||'Tất cả các khoản chuyển khoản đã chốt'}</p><div class="stats">Số đơn nguồn: <b>${data.count}</b> · Tổng chuyển khoản: <b>${fmt(data.total)}</b> đ<br>Chưa đối chiếu: ${fmt(data.status_totals.CHUA_DOI_CHIEU)} · Đã khớp: ${fmt(data.status_totals.DA_KHOP)} · Chênh lệch: ${fmt(data.status_totals.CHENH_LECH)}</div>
  ${data.warning_count?`<p class="warning">${data.warning_count} dòng có cảnh báo dữ liệu. Xem cột ghi chú trước khi xác nhận.</p>`:''}
  <table><thead><tr>${cols.map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${data.rows.map((r,i)=>`<tr data-id="${r.id}"><td>${i+1}</td><td>${esc(r.settlement_date)}<br>${esc(r.settled_at.slice(11))}</td>
  <td>${edit&&canEdit?`<input class="sd" type="date" value="${esc(r.statement_date)}">`:esc(r.statement_date||'Chưa có')}</td>
  <td>${esc(r.customer)}${[r.customer_dms,r.customer_mbw].filter(x=>x&&x!==r.customer).map(x=>'<br>'+esc(x)).join('')}</td>
  <td>${esc(r.customer_name)}</td><td>${esc(r.order)}</td><td>${esc(r.lot)}<br>${esc(r.session)}</td><td>${esc(r.staff)}<br>${esc(r.staff_name)}</td>
  <td>${esc(r.bank_name)}<br>${esc(r.account)}</td><td>${esc(r.txn)}</td><td class="money">${fmt(r.amount)}</td>
  <td>${edit&&canEdit?`<select class="status">${Object.entries(statuses).map(([k,v])=>`<option value="${k}" ${r.status===k?'selected':''}>${v}</option>`).join('')}</select>`:esc(statuses[r.status])}<br><small>${esc(r.updated_by)} ${esc(r.updated_at)}</small></td>
  <td>${edit&&canEdit?`<textarea class="note" maxlength="2000" style="width:160px">${esc(r.note)}</textarea><br><button class="save">Lưu đối chiếu</button>`:esc(r.note)}${r.warnings.map(w=>'<div class="warning">'+esc(w)+'</div>').join('')}</td></tr>`).join('')||'<tr><td colspan="13">Không có khoản chuyển khoản trong bộ lọc này.</td></tr>'}</tbody><tfoot><tr><th colspan="10">Tổng chuyển khoản theo bộ lọc</th><th class="money">${fmt(data.total)}</th><th colspan="2"></th></tr></tfoot></table>
  <p>Mỗi dòng là số tiền chuyển khoản phân bổ cho một đơn nguồn. Đối chiếu sao kê không tạo thêm phiếu thu, không thay đổi công nợ hoặc quỹ.</p>
  ${edit?'':'<div class="sign"><span>Người lập báo cáo</span><span>Kế toán ngân hàng đối chiếu</span><span>Kế toán trưởng</span></div>'}`;
 }
 async function load(){el('brError').textContent='';el('brPrint').disabled=el('brExport').disabled=true;el('brLoad').disabled=true;
  try{const p=params();data=await api(root+'?'+p);loadedParams=p;const old=el('brBank').value;
   el('brBank').innerHTML='<option value="">Tất cả</option>'+data.banks.map(b=>`<option value="${esc(b.key)}">${esc(b.label)}</option>`).join('');el('brBank').value=old;
   el('brBody').innerHTML=content(true);el('brPrint').disabled=el('brExport').disabled=pending.size>0;
   for(const [id,v] of pending){const tr=el('brBody').querySelector('tr[data-id="'+id+'"]');if(tr&&canEdit){tr.querySelector('.status').value=v.status;tr.querySelector('.sd').value=v.statement_date;tr.querySelector('.note').value=v.note;}}
   if(pending.size)el('brError').textContent='Có '+pending.size+' dòng chưa lưu. Lưu từng dòng trước khi in hoặc xuất file.';
   el('brBody').querySelectorAll('.save').forEach(btn=>btn.onclick=async()=>{const tr=btn.closest('tr');const r=data.rows.find(x=>x.id===Number(tr.dataset.id));btn.disabled=true;
    try{await api(root+'/'+r.id+'/reconcile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:tr.querySelector('.status').value,statement_date:tr.querySelector('.sd').value,note:tr.querySelector('.note').value,version:r.version,fingerprint:r.fingerprint})});pending.delete(r.id);await load();}
    catch(e){el('brError').textContent=e.message;btn.disabled=false;}
   });
  }catch(e){data=null;el('brBody').innerHTML='';el('brError').textContent=e.message;}finally{el('brLoad').disabled=false;}
 }
 el('brLoad').onclick=load;
 el('brBody').addEventListener('input',e=>{const tr=e.target.closest('tr[data-id]');if(!tr)return;pending.set(Number(tr.dataset.id),{status:tr.querySelector('.status').value,statement_date:tr.querySelector('.sd').value,note:tr.querySelector('.note').value});el('brPrint').disabled=el('brExport').disabled=true;el('brError').textContent='Có thay đổi chưa lưu. Lưu đối chiếu từng dòng trước khi in hoặc xuất file.';});
 dlg.querySelectorAll('input,select').forEach(x=>x.addEventListener('change',()=>{el('brPrint').disabled=el('brExport').disabled=true;}));
 el('brPrint').onclick=()=>{if(!data||params()!==loadedParams){el('brError').textContent='Bộ lọc đã đổi; bấm Tra cứu trước khi in.';return;}
  const w=window.open('','_blank');if(!w){el('brError').textContent='Cho phép cửa sổ bật lên để in.';return;}
  w.document.write(`<!doctype html><html lang="vi"><meta charset="utf-8"><title>Mã Ngân Hàng</title><style>@page{size:A4 landscape;margin:9mm}body{font:10px Arial}h1,h2{text-align:center}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border:1px solid #64748b;padding:4px;overflow-wrap:anywhere;vertical-align:top}.money{text-align:right}thead{display:table-header-group}tr{break-inside:avoid}.stats{padding:10px;background:#edf5f6}.warning{color:#92400e}.sign{display:flex;justify-content:space-around;margin:30px 0 60px}@media print{button{display:none}}</style><button onclick="window.print()">In / Lưu PDF</button>${content(false)}</html>`);w.document.close();w.focus();w.print();
 };
 el('brExport').onclick=async()=>{if(!data||params()!==loadedParams)return;el('brExport').disabled=true;
  try{const token=localStorage.getItem('vg_token');const r=await fetch(root+'/export.xlsx?'+loadedParams,{headers:token?{Authorization:'Bearer '+token}:{}});
   if(!r.ok){const x=await r.json();throw Error(x.detail||'Không xuất được file.');}const a=document.createElement('a');a.href=URL.createObjectURL(await r.blob());a.download='MA_NGAN_HANG.xlsx';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
  }catch(e){el('brError').textContent=e.message;}finally{el('brExport').disabled=false;}
 };
 try{const profile=await api('/api/access/profile');canEdit=profile.screen_permissions?.QTGH_UI04==='EDIT';await load();}catch(e){el('brError').textContent=e.message;}
};
