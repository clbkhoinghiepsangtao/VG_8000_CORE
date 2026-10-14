(function(){
 const day=document.getElementById('misaInvoiceDate');
 const button=document.getElementById('exportMisaLot');
 if(!day||!button)return;
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
 const datePart=t=>parts.find(x=>x.type===t).value;
 day.value=datePart('year')+'-'+datePart('month')+'-'+datePart('day');
 button.onclick=async()=>{
  const lots=[...document.querySelectorAll('.vehicle-pick-lot:checked')].map(x=>x.value);
  if(lots.length!==1){alert('Chọn đúng một lô để xuất MISA đủ cả ba kho.');return;}
  if(document.querySelector('.pick-order:checked')){alert('Bỏ chọn các đơn riêng. Xuất MISA lấy toàn bộ một lô đã chọn.');return;}
  if(!day.value){alert('Chọn ngày hóa đơn để lấy bảng giá hiệu lực.');return;}
  button.disabled=true;
  try{
   const url='/api/qtgh-v11/print-lot/'+encodeURIComponent(lots[0])+'/misa-export.xlsx?invoice_date='+encodeURIComponent(day.value);
   const response=await fetch(url,{headers:{Authorization:'Bearer '+(localStorage.getItem('vg_token')||'')},cache:'no-store'});
   if(!response.ok){let x={};try{x=await response.json()}catch(e){}throw new Error(x.detail||('HTTP '+response.status));}
   const blob=await response.blob();const objectURL=URL.createObjectURL(blob);
   const link=document.createElement('a');link.href=objectURL;link.download='MISA_'+lots[0]+'_'+day.value+'.xlsx';document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(objectURL),30000);
  }catch(e){alert('Không xuất được MISA: '+e.message);}
  finally{button.disabled=false;}
 };
})();
