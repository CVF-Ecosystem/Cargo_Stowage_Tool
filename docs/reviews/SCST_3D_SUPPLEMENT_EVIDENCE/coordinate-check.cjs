const {chromium,expect}=require(process.cwd()+'/apps/frontend/node_modules/@playwright/test');
const fs=require('fs');
(async()=>{
 const db='runtime-data/scst.sqlite3';const before=fs.existsSync(db)?fs.readFileSync(db):null;
 const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-webgl']});
 const near=(a,b)=>expect(Math.abs(a-b)).toBeLessThan(0.00001);
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1100}});
  const profile=await(await page.request.get('http://127.0.0.1:8765/api/vessels/vinafco268')).json();
  const g=profile.geometry,h=profile.hold;
  const sourceCentre=(g.source_hold_x_min_m+g.source_hold_x_max_m)/2;
  const expectedTranslation=[profile.dimensions_m.length/2-sourceCentre,-g.source_floor_z_m,0];
  expectedTranslation.forEach((v,i)=>near(g.glb_to_hold_translation_m[i],v));
  await page.goto('http://127.0.0.1:8765');
  const response=page.waitForResponse(r=>r.url().endsWith('/api/validate')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Xem VINAFCO 268'}).click();
  const validated=await response;expect(validated.ok()).toBe(true);const evaluated=await validated.json();
  const canvas=page.getByTestId('three-canvas');
  await expect.poll(()=>canvas.getAttribute('data-vessel-bounds')).not.toBeNull();
  const bounds=JSON.parse(await canvas.getAttribute('data-vessel-bounds'));
  expectedTranslation.forEach((v,i)=>near(bounds.position[i],v));
  const convert=([x,y,z])=>[x-profile.dimensions_m.length/2+bounds.position[0],z+bounds.position[1],-y+bounds.position[2]];
  const checkPoints=[
   {source:[40,1,2],scene:[0.1275,1.168,-1]},
   {source:[sourceCentre,0,g.source_floor_z_m],scene:[0,0,0]},
   {source:[g.source_hold_x_min_m,0,g.source_floor_z_m],scene:[-h.length_mm/2000,0,0]},
   {source:[g.source_hold_x_max_m,0,g.source_floor_z_m],scene:[h.length_mm/2000,0,0]},
   {source:[sourceCentre,g.source_hold_y_max_m,g.source_floor_z_m],scene:[0,0,-h.source_width_m/2]},
   {source:[sourceCentre,g.source_hold_y_min_m,g.source_floor_z_m],scene:[0,0,h.source_width_m/2]}
  ];
  for(const p of checkPoints)convert(p.source).forEach((v,i)=>near(v,p.scene[i]));
  near(h.source_width_m*1000-h.width_mm,g.width_inset_each_side_mm*2);
  const meshes=JSON.parse(await canvas.getAttribute('data-meshes'));
  expect(meshes.length).toBe(evaluated.plan.placements.length);
  for(const p of evaluated.plan.placements){
   const u=evaluated.plan.units.find(u=>u.id===p.unit_id),mesh=meshes.find(m=>m.id===p.unit_id);
   const d=u.dimensions_um?u.dimensions_um.map(v=>v/1000000):[u.length_mm/1000,u.width_mm/1000,u.height_mm/1000];
   const [dx,dy]=p.yaw_deg%180?[d[1],d[0]]:[d[0],d[1]],dz=d[2];
   const position=[p.x_mm/1000+dx/2-h.length_mm/2000,p.z_mm/1000+dz/2,p.y_mm/1000+dy/2-h.width_mm/2000];
   position.forEach((v,i)=>{near(mesh.position[i],v);near(mesh.worldMatrix[12+i],v)});
   [dx,dz,dy].forEach((v,i)=>near(mesh.dimensions[i],v));
  }
  near(bounds.max[0]-bounds.min[0],77.8);
  expect(fs.existsSync(db)?fs.readFileSync(db):null).toEqual(before);
  const result={status:'PASS',scope:'Read-only coordinate verification before roadmap consolidation; no runtime repair required',runtime:'http://127.0.0.1:8765',json_to_glb_formula:['x-38.9','z','-y'],glb_to_actual_scene_translation_m:bounds.position,source_point_m:[40,1,2],glb_point_m:[1.1,2,-1],actual_scene_point_m:checkPoints[0].scene,anchor_points_checked:checkPoints.length,cargo_meshes_checked:meshes.length,source_hold_floor_center_maps_to_scene_origin:true,hold_boundary_axes_checked:true,source_width_inset_is_existing_conservative_conversion:true,user_database_unchanged:true};
  fs.writeFileSync('.cvf/runtime/coordinate-audit.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
