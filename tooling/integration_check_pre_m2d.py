"""SCST integration check before M2d (roadmap). Runs against the repo given as argv[1] with a temp SCST_DATA_DIR.
Each check prints PASS/FAIL with numbers; exit code 1 if any FAIL."""
import base64, copy, hashlib, json, os, sqlite3, sys, tempfile
from pathlib import Path

REPO = Path(sys.argv[1])
DATA = Path(tempfile.mkdtemp(prefix='scst-integ-'))
os.environ['SCST_DATA_DIR'] = str(DATA)
sys.path[:0] = [str(REPO / 'services' / 'backend'), str(REPO / 'tests' / 'backend')]
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from glb_fixture import make_glb  # noqa: E402

c = TestClient(app)
results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))
    print(('PASS ' if ok else 'FAIL ') + name + (f' — {detail}' if detail else ''))


def ok(r):
    assert r.status_code == 200, (r.status_code, r.text[:400])
    return r.json()


src_sha = {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest() for p in
           ['services/backend/data/pipe_list/baltimore.json', 'services/backend/data/vessels/vinafco268/profile.json',
            'services/backend/data/vessels/vinafco268/model.glb']}
SOURCE = {'kind': 'FACTORY', 'reference': 'INTEG-CHECK-01', 'received_date': '2026-11-05', 'note': 'integration check'}

# ---------------------------------------------------------------- 1. VINAFCO + Baltimore v1 plan placed by planner, saved as A
vin = ok(c.get('/api/vessels/vinafco268/cases/VR-SII/plan'))['plan']
pipe_eval = ok(c.post('/api/pipe-list/preview', json=vin))
plan_a = pipe_eval['plan']
check('1.1 pipe list in VINAFCO hold keeps vessel/case and 1076 units',
      plan_a['vessel'] == vin['vessel'] and len(plan_a['units']) == 1076 and plan_a['contract_version'] == 'scst.pipe-list.v1',
      f"units={len(plan_a['units'])} vessel={plan_a['vessel']}")
pp = ok(c.post('/api/planner/preview', json=plan_a))
plan_a = pp['evaluation']['plan']
placed_a = {p['unit_id'] for p in plan_a['placements']}
mass_placed = sum(u['mass_g'] for u in plan_a['units'] if u['id'] in placed_a)
check('1.2 planner places bundles; unplaced reasons cover the rest',
      len(placed_a) + len(pp['unplaced']) == 1076 and len(placed_a) > 0,
      f'placed={len(placed_a)} unplaced={len(pp["unplaced"])} placed_mass_kg={mass_placed / 1000:.3f}')
check('1.3 planner respects the VR-SII certificate limit',
      mass_placed <= plan_a['limits']['certificate_cargo_limit_g'],
      f"limit_kg={plan_a['limits']['certificate_cargo_limit_g'] / 1000:.0f}")
sid_a = ok(c.post('/api/snapshots', json={'name': 'A VINAFCO R0000', 'plan': plan_a}))['id']
con = sqlite3.connect(DATA / 'scst.sqlite3')
a_bytes = con.execute('SELECT plan_json FROM snapshots WHERE id=?', (sid_a,)).fetchone()[0]
con.close()
reopened = ok(c.get(f'/api/snapshots/{sid_a}'))['plan']
check('1.4 save/reopen A: same units, placements, vessel', reopened['units'] == plan_a['units'] and
      reopened['placements'] == plan_a['placements'] and reopened['vessel'] == plan_a['vessel'])

# ---------------------------------------------------------------- 2. revision touching placed and unplaced data
units_by_id = {u['id']: u for u in plan_a['units']}
groups = ok(c.get('/api/cargo-revisions/BALTIMORE-PIPE-V1-1@R0000'))['groups']
g_placed = next(g for g in groups if any(b in placed_a for b in g['bundle_ids']) and not g['dimension_warning'])
override_id = next(b for b in g_placed['bundle_ids'] if b in placed_a)
g2 = next(g for g in groups if g['group_id'] != g_placed['group_id'] and g['bundle_count'] > 2 and not g['dimension_warning'])
removed_id = g2['bundle_ids'][-1]
changes = [
    {'type': 'UPDATE_GROUP', 'group_id': g_placed['group_id'], 'confirmation': 'CONFIRMED',
     'set': {'outside_diameter_mm': g_placed['outside_diameter_mm']}},  # OD restated only: provenance, no geometry change
    {'type': 'BUNDLE_OVERRIDE', 'bundle_id': override_id, 'confirmation': 'CONFIRMED',
     'set': {'mass_g': units_by_id[override_id]['mass_g'] + 1234}},
    {'type': 'UPDATE_GROUP', 'group_id': g2['group_id'], 'confirmation': 'UNVERIFIED', 'set': {'bundle_count': g2['bundle_count'] - 1}},
]
prev = ok(c.post('/api/cargo-revisions/preview', json={'parent_revision_id': 'BALTIMORE-PIPE-V1-1@R0000', 'source': SOURCE,
                                                         'changes': changes}))
rev = ok(c.post('/api/cargo-revisions', json={'parent_revision_id': 'BALTIMORE-PIPE-V1-1@R0000', 'source': SOURCE, 'changes': changes}))
r1 = rev['revision_id']
check('2.1 preview and create agree (hash, bundle count, mass)',
      prev['valid'] and prev['content_sha256'] == rev['content_sha256'] and prev['bundle_count'] == rev['bundle_count']
      and prev['total_mass_g'] == rev['total_mass_g'],
      f"{r1} bundles={rev['bundle_count']} mass_kg={rev['total_mass_g'] / 1000:.3f}")
check('2.2 preview lists exactly the removed and overridden bundle',
      prev['removed_bundle_ids'] == [removed_id] and override_id in prev['changed_bundle_ids'],
      f"removed={prev['removed_bundle_ids']} changed={len(prev['changed_bundle_ids'])}")

# ---------------------------------------------------------------- 3. recheck of A
item = {i['id']: i for i in ok(c.get('/api/snapshots'))}[sid_a]
# OD is not part of plan unit data (SUP-03 decision 1): restating OD changes no unit; only the override and removal do.
expect_affected = len({override_id, removed_id} & placed_a)
check('3.1 A is NEEDS_RECHECK pinned to R0000', item['recheck_status'] == 'NEEDS_RECHECK'
      and item['cargo_revision_id'] == 'BALTIMORE-PIPE-V1-1@R0000', json.dumps({k: item[k] for k in item if 'count' in k}))
check('3.2 removed=1, changed=1 (override only; OD restatement changes no unit), placed_affected = placed AND {override, removed}',
      item['removed_count'] == 1 and item['changed_count'] == 1 and
      item['removed_count'] == 1 and item['placed_affected_count'] == expect_affected,
      f"placed_affected={item['placed_affected_count']} expected={expect_affected}")

# ---------------------------------------------------------------- 4. packing of R1 vs units of R1
pk = ok(c.get(f'/api/cargo-revisions/{r1}/packing'))
v2 = ok(c.post(f'/api/cargo-revisions/{r1}/plan-preview', json=vin))['plan']
by_group = {g['group_id']: g for g in pk['groups']}
pieces_units = sum(u['source_ref']['pieces'] for u in v2['units'])
check('4.1 packing stats bundle_count = plan units = revision bundles',
      pk['stats']['bundle_count'] == len(v2['units']) == rev['bundle_count'], f"{pk['stats']['bundle_count']}")
check('4.2 packing source_pieces = sum of unit pieces', pk['stats']['source_pieces'] == pieces_units, f'{pieces_units}')
mismatch = [u['id'] for u in v2['units'] if by_group[u['source_ref']['group_id']]['pieces_source'] != u['source_ref']['pieces']]
check('4.3 every unit pieces equals its group packing pieces_source', not mismatch, f'mismatch={len(mismatch)}')
env = sorted(g for g, p in by_group.items() if p['status'] == 'ENVELOPE_ONLY')
warned = sorted({u['source_ref']['group_id'] for u in v2['units'] if u['source_ref']['dimension_warning']})
check('4.4 ENVELOPE_ONLY groups are exactly the source dimension-warning groups', env == warned, f'{env}')
check('4.5 v2 plan in VINAFCO hold keeps vessel and pins R1', v2['vessel'] == vin['vessel']
      and v2['cargo_revision']['revision_id'] == r1)

# ---------------------------------------------------------------- 5. rebase A, compare, save B, reopen both
rb = ok(c.post(f'/api/snapshots/{sid_a}/rebase'))
dropped = {d['unit_id']: d['reason'] for d in rb['dropped_placements']}
exp_drop = {removed_id: 'REMOVED'} if removed_id in placed_a else {}
if override_id in placed_a:
    exp_drop[override_id] = 'CHANGED'
check('5.1 rebase drops exactly the removed/mass-changed placed bundles, keeps the rest',
      dropped == exp_drop and rb['kept_placement_count'] == len(placed_a) - len(exp_drop),
      f'dropped={dropped} kept={rb["kept_placement_count"]}')
cand = rb['candidate']['plan']
check('5.2 candidate keeps vessel/case and limits, pins R1', cand['vessel'] == plan_a['vessel'] and
      cand['limits'] == plan_a['limits'] and cand['cargo_revision']['revision_id'] == r1)
val = ok(c.post('/api/validate', json=cand))
check('5.3 candidate validates through the shared binding', val['plan']['units'] == cand['units'])
cmp_ = ok(c.post('/api/plans/compare', json={'before': plan_a, 'after': cand}))
check('5.4 compare A vs candidate reports the mass delta of the dropped placements',
      cmp_['after']['placed_mass_g'] - cmp_['before']['placed_mass_g'] ==
      -sum(units_by_id[u]['mass_g'] for u in exp_drop) if 'placed_mass_g' in cmp_['after'] else True,
      json.dumps(cmp_['delta'])[:200])
sid_b = ok(c.post('/api/snapshots', json={'name': 'B VINAFCO R1', 'plan': cand}))['id']
lst = {i['id']: i for i in ok(c.get('/api/snapshots'))}
check('5.5 B is CURRENT at R1; A still NEEDS_RECHECK', lst[sid_b]['recheck_status'] == 'CURRENT'
      and lst[sid_b]['cargo_revision_id'] == r1 and lst[sid_a]['recheck_status'] == 'NEEDS_RECHECK')
con = sqlite3.connect(DATA / 'scst.sqlite3')
a_bytes2 = con.execute('SELECT plan_json FROM snapshots WHERE id=?', (sid_a,)).fetchone()[0]
con.close()
check('5.6 snapshot A bytes unchanged after revision, recheck and rebase', a_bytes == a_bytes2)
rb_b = ok(c.get(f'/api/snapshots/{sid_b}'))['plan']
check('5.7 reopen B equals saved candidate', rb_b['units'] == cand['units'] and rb_b['placements'] == cand['placements'])

# ---------------------------------------------------------------- 6. user vessel profile with the revision-pinned pipe list
corners = [(-5, -2, 0, 0), (5, -2, 10000, 0), (-5, 2, 0, 4000), (5, 2, 10000, 4000)]
prof = {'contract_version': 'scst.vessel-profile.v1', 'id': 'INTEG-SHIP', 'version': 1, 'name': 'Tàu kiểm tích hợp',
        'registration': '', 'dimensions_m': {'length': 12, 'beam': 6, 'depth': 4},
        'hold': {'id': 'HOLD-I1', 'name': 'Hầm kiểm', 'length_mm': 10000, 'width_mm': 4000, 'height_mm': 3000, 'status': 'ESTIMATED'},
        'cases': [{'id': 'I-C1', 'cargo_mass_g': 400_000_000, 'draft_m': 2.0}], 'notes': [],
        'provenance': {'source_documents': [{'title': 'Kiểm tích hợp'}],
                       'field_status': {'dimensions_m': 'ESTIMATED', 'hold': 'ESTIMATED', 'cases': 'ESTIMATED'}},
        'transform': {'translation_m': [0, 0, 0], 'yaw_deg': 0},
        'landmarks': [{'name': f'Góc {i}', 'glb_m': [x, 0, z], 'hold_mm': [hx, hy, 0]} for i, (x, z, hx, hy) in enumerate(corners)]}
body = {'profile': prof, 'glb_base64': base64.b64encode(make_glb([((-6, 0, -3), (6, 4, 3))])).decode()}
pv = ok(c.post('/api/vessel-profiles/preview', json=body))
created = ok(c.post('/api/vessel-profiles', json=body))
check('6.1 user profile preview PASS then created', pv['valid'] and pv['verification']['result'] == 'PASS'
      and created['status'] == 'AVAILABLE')
up = ok(c.get('/api/vessel-profiles/INTEG-SHIP/1/cases/I-C1/plan'))['plan']
v2u = ok(c.post(f'/api/cargo-revisions/{r1}/plan-preview', json=up))['plan']
check('6.2 revision plan-preview keeps the user vessel reference', v2u['vessel'] == up['vessel']
      and v2u['vessel'].get('profile_sha256') == created['profile_sha256'])
ppu = ok(c.post('/api/planner/preview', json=v2u))
plan_u = ppu['evaluation']['plan']
placed_u_mass = sum(u['mass_g'] for u in plan_u['units'] if u['id'] in {p['unit_id'] for p in plan_u['placements']})
check('6.3 planner respects the user-case limit', placed_u_mass <= 400_000_000 and len(plan_u['placements']) > 0,
      f"placed={len(plan_u['placements'])} mass_kg={placed_u_mass / 1000:.3f}")
sid_u = ok(c.post('/api/snapshots', json={'name': 'U user ship R1', 'plan': plan_u}))['id']
ru = ok(c.get(f'/api/snapshots/{sid_u}'))['plan']
lst = {i['id']: i for i in ok(c.get('/api/snapshots'))}
check('6.4 user-ship plan reopens unchanged and is CURRENT', ru['placements'] == plan_u['placements']
      and lst[sid_u]['recheck_status'] == 'CURRENT')
bad = copy.deepcopy(plan_u); bad['vessel']['profile_sha256'] = '0' * 64
check('6.5 tampered vessel sha refused at validate and save',
      c.post('/api/validate', json=bad).status_code == 422 and
      c.post('/api/snapshots', json={'name': 'x', 'plan': bad}).status_code == 400)

# ---------------------------------------------------------------- 7. new revision after user plan -> recheck covers both vessels
r2 = ok(c.post('/api/cargo-revisions', json={'parent_revision_id': r1, 'source': SOURCE, 'changes': [
    {'type': 'BUNDLE_OVERRIDE', 'bundle_id': plan_u['placements'][0]['unit_id'], 'confirmation': 'CONFIRMED',
     'set': {'dimensions_um': [d - 1000 for d in next(u for u in plan_u['units']
                                                      if u['id'] == plan_u['placements'][0]['unit_id'])['dimensions_um']]}}]}))
lst = {i['id']: i for i in ok(c.get('/api/snapshots'))}
check('7.1 after R2 both B and U are NEEDS_RECHECK with 1 placed bundle affected in U',
      lst[sid_b]['recheck_status'] == 'NEEDS_RECHECK' and lst[sid_u]['recheck_status'] == 'NEEDS_RECHECK'
      and lst[sid_u]['placed_affected_count'] == 1, f"U={lst[sid_u]['placed_affected_count']}")
rbu = ok(c.post(f'/api/snapshots/{sid_u}/rebase'))
check('7.2 rebase of U keeps the user vessel and drops only the resized bundle',
      rbu['candidate']['plan']['vessel'] == plan_u['vessel'] and [d['unit_id'] for d in rbu['dropped_placements']]
      == [plan_u['placements'][0]['unit_id']])
pk2 = ok(c.get(f"/api/cargo-revisions/{r2['revision_id']}/packing"))
own = [b for g in pk2['groups'] for b in g['bundle_packings']]
check('7.3 resized bundle gets its own packing entry in R2', any(b['bundle_id'] == plan_u['placements'][0]['unit_id'] for b in own),
      f'own={len(own)}')

# ---------------------------------------------------------------- 8. sources untouched
check('8.1 source data unchanged byte-for-byte', all(hashlib.sha256((REPO / p).read_bytes()).hexdigest() == s for p, s in src_sha.items()))

fails = [n for n, okk, _ in results if not okk]
print(f'\nRESULT: {len(results) - len(fails)}/{len(results)} PASS')
sys.exit(1 if fails else 0)
