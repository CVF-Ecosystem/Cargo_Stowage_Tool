// Independent integer expectations against actual UI helpers. No backend mutation.
const fs=require('fs'),assert=require('assert');
const ts=require(process.cwd()+'/apps/frontend/node_modules/typescript');
const out='docs/reviews/SCST_DISPLAY_UNITS_EVIDENCE/';
let checks=0;const eq=(a,b)=>{assert.deepStrictEqual(a,b);checks++};
function execute(source,model={}){const mod={exports:{}};const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;new Function('module','exports','model',js)(mod,mod.exports,model);return mod.exports;}
const model=execute(fs.readFileSync('apps/frontend/src/features/model.ts','utf8'));
function helpers(path,names,extra=''){
 const text=fs.readFileSync(path,'utf8'),ast=ts.createSourceFile(path,text,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
 const selected=ast.statements.filter(s=>(ts.isFunctionDeclaration(s)&&names.includes(s.name?.text))||(ts.isVariableStatement(s)&&s.declarationList.declarations.some(d=>d.name.getText(ast)==='valueLabels'))).map(s=>s.getText(ast)).join('\n');
 return execute('const {'+Object.keys(model).join(',')+'}=model;\n'+selected+'\n'+extra,model);
}
const draft=helpers('apps/frontend/src/features/Workspace.tsx',['draftFrom','markDirty','applyDraft','rebaseDraft']);
const panel=helpers('apps/frontend/src/features/ComparisonPanel.tsx',['valueText','smallDifference'],'exports.valueText=valueText;exports.smallDifference=smallDifference;');
const round=(n,divisor)=>{const abs=BigInt(Math.abs(n));return Number((abs+BigInt(divisor/2))/BigInt(divisor))*(n<0?-1:1)};
const vi=n=>new Intl.NumberFormat('vi-VN',{maximumFractionDigits:0}).format(n);
(async()=>{
 for(let n=-100005;n<=100005;n+=137){
  eq(model.displayKg(n),String(round(n,1000)));eq(model.displayCm(n),String(round(n,10)));
  eq(model.formatKg(n),n!==0&&Math.abs(n)<1000?(n<0?'-<1':'<1'):vi(round(n,1000)));
  eq(model.formatCm(n),n!==0&&Math.abs(n)<10?(n<0?'-<1':'<1'):vi(round(n,10)));
 }
 for(const mm of [-1000000,-501,-5,-1,0,1,5,501,1000000])eq(model.parseCm(String(mm/10)),mm);
 eq(model.parseCm('51,2'),512);
 for(const bad of ['51.23','abc','1e2','100000.1','-100000.1','']){assert.throws(()=>model.parseCm(bad));checks++;}
 eq(model.formatCm(337.6),'34');eq(model.formatMetres(77800),'77,8');eq(model.formatKg(911400),'911');
 const response=await fetch('http://127.0.0.1:8765/api/demo');assert(response.ok);const demo=(await response.json()).plan;
 for(let i=0;i<120;i++){
  const p=structuredClone(demo);p.contract_version='scst.m2a.v1';p.cargo_source='USER_ENTERED';const id=p.units[0].id;
  p.units[0].mass_g=2500001+i*7;p.units[0].length_mm=6401+i;p.placements[0].x_mm=501+i;p.hold.length_mm=14001+i;
  p.limits.certificate_cargo_limit_g+=i+1;p.limits.voyage_cargo_limit_g+=i+1;p.limits.cargo_onboard_g=i+1;
  const initial=structuredClone(p),d=draft.draftFrom(p);
  eq(draft.applyDraft(p,d),p);eq(p,initial);
  d.units[id].yaw='90';d.dirty[`unit.${id}.yaw`]=true;
  const expected=structuredClone(p);expected.placements[0].yaw_deg=90;
  eq(draft.applyDraft(p,d),expected);eq(p,initial);
  d.units[id].mass=model.displayKg(p.units[0].mass_g);d.dirty=draft.markDirty(d.dirty,`unit.${id}.mass`,d.units[id].mass,p.units[0].mass_g,model.parseKg);
  assert(d.dirty[`unit.${id}.mass`]);checks++;
  expected.units[0].mass_g=round(p.units[0].mass_g,1000)*1000;
  eq(draft.applyDraft(p,d),expected);
  d.dirty=draft.markDirty(d.dirty,`unit.${id}.mass`,model.kgInput(p.units[0].mass_g),p.units[0].mass_g,model.parseKg);
  eq(d.dirty[`unit.${id}.mass`],undefined);
  d.units[id].x='51.2';d.dirty[`unit.${id}.x`]=true;expected.units[0].mass_g=p.units[0].mass_g;expected.placements[0].x_mm=512;
  eq(draft.applyDraft(p,d),expected);
 }
 const p=structuredClone(demo);p.contract_version='scst.m2a.v1';p.cargo_source='USER_ENTERED';p.units[0].mass_g=2500001;p.placements[0].x_mm=501;p.placements.reverse();
 eq(draft.applyDraft(p,draft.draftFrom(p)),p);
 const uid=p.units[0].id,sent=draft.draftFrom(p);sent.units[uid].mass='2501';sent.dirty[`unit.${uid}.mass`]=true;
 const checked=draft.applyDraft(p,sent),late=structuredClone(sent);late.units[uid].mass='2500.001';late.dirty=draft.markDirty(late.dirty,`unit.${uid}.mass`,late.units[uid].mass,p.units[0].mass_g,model.parseKg);
 const rebased=draft.rebaseDraft(late,sent,p,checked);eq(Boolean(rebased.dirty[`unit.${uid}.mass`]),true);eq(draft.applyDraft(checked,rebased).units[0].mass_g,2500001);
 const yawSent=draft.draftFrom(p);yawSent.units[uid].yaw='90';yawSent.dirty[`unit.${uid}.yaw`]=true;const yawChecked=draft.applyDraft(p,yawSent),sameText=structuredClone(yawSent);
 sameText.dirty=draft.markDirty(sameText.dirty,`unit.${uid}.mass`,sameText.units[uid].mass,p.units[0].mass_g,model.parseKg);
 eq(draft.applyDraft(yawChecked,draft.rebaseDraft(sameText,yawSent,p,yawChecked)).units[0].mass_g,2500000);
 const renamed=draft.draftFrom(p);renamed.units[uid].id='NEW-ID';renamed.dirty[`unit.${uid}.id`]=true;const renamedChecked=draft.applyDraft(p,renamed),later=structuredClone(renamed);later.units[uid].x='52';later.dirty[`unit.${uid}.x`]=true;
 const reId=draft.applyDraft(renamedChecked,draft.rebaseDraft(later,renamed,p,renamedChecked));eq(reId.placements.find(q=>q.unit_id==='NEW-ID').x_mm,520);eq(reId.units[0].mass_g,2500001);
 const source=await(await fetch('http://127.0.0.1:8765/api/pipe-list/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(demo)})).json();
 const original=structuredClone(source.plan),d=draft.draftFrom(original),id=original.units[0].id;
 d.units[id].requirement='required';d.dirty[`unit.${id}.requirement`]=true;
 const expected=structuredClone(original);expected.units[0].requirement='required';eq(draft.applyDraft(original,d),expected);
 eq(original,source.plan);eq(original.units.length,1076);
 for(const [field,before,after,unit] of [['mass_g',2500000,2500001,'kg'],['placement.x_mm',500,501,'cm'],['dimensions_um',[1000000,337600,100000],[1000001,337601,100001],'cm']]){
  const c={field,before,after};assert(panel.smallDifference(c)?.includes('dưới 1 '+unit));checks++;
  eq(panel.valueText(before,field),panel.valueText(after,field));
 }
 eq(panel.valueText(2500001,'mass_g'),'2.500');eq(panel.valueText(501,'placement.x_mm'),'50');eq(panel.valueText([6401000,337600,295400],'dimensions_um'),'640 × 34 × 30');
 const result={status:'PASS',assertions:checks,randomized_exact_drafts:120,source_units:1076,method:'Independent BigInt round/conversion expectations and copied Plan field expectations; actual TS helpers extracted unchanged via TypeScript AST',backend_or_user_db_writes:false};
 fs.writeFileSync(out+'root-numeric.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
