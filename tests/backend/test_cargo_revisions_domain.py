import copy
import pytest
from app.adapters import pipe_registry
from app.domain import cargo_revisions as cr
from app.domain.model import CargoUnit

REG = pipe_registry.REGISTRY
BASE_SHA = '9392efc3fd93d9b56e2bfddb2cf45c73d04755d7fe1003092b09fca5250449a4'
SRC = {'kind': 'FACTORY', 'reference': 'Phiếu cân 2026-11-01', 'received_date': '2026-11-01', 'note': 'ghi chú'}
G2, G22 = 'Sheet1-R002', 'Sheet1-R022'  # R002: 160 bundles, no warning. R022: 12 bundles, dimension_warning true


def base():
    return cr.base_groups(REG)


def gs(groups, gid):
    return next(g for g in groups if g['group_id'] == gid)


def upd(gid=G2, conf='CONFIRMED', **s):
    return {'type': 'UPDATE_GROUP', 'group_id': gid, 'confirmation': conf, 'set': s}


def add(conf='UNVERIFIED', **over):
    g = {'bundle_count': 3, 'pieces_per_bundle': 7, 'dimensions_um': [1000, 2000, 3000], 'mass_g': 500,
         'outside_diameter_mm': '10.5', 'wall_thickness_mm': '2', 'dimension_warning': False}
    g.update(over)
    return {'type': 'ADD_GROUP', 'confirmation': conf, 'group': g}


def ovr(bid, conf='CONFIRMED', **s):
    return {'type': 'BUNDLE_OVERRIDE', 'bundle_id': bid, 'confirmation': conf, 'set': s}


def apply(changes, groups=None, rev=1, source=SRC):
    return cr.apply_batch(groups or base(), source, changes, cr.revision_id(rev))


def errs(changes, groups=None, source=SRC):
    return cr.validate_batch(groups or base(), source, changes)


def one(changes, **kw):
    e = errs(changes, **kw)
    assert len(e) == 1, e
    assert e[0]['message'] and any(ch.isalpha() and ord(ch) > 127 or ' ' in e[0]['message'] for ch in e[0]['message'])
    return e[0]


def record(rev, parent, source, changes, groups):
    return {'revision_id': cr.revision_id(rev), 'parent_revision_id': parent, 'source': source, 'changes': changes,
            'content_sha256': cr.content_sha256(groups), 'created_utc': '2026-11-04T00:00:00Z'}


def two_revisions():
    g1, _, _ = apply([upd(mass_g=912000)], rev=1)
    c2 = [add(), ovr('PIPE-R002-B0002', mass_g=900000)]
    g2, _, _ = apply(c2, g1, rev=2)
    return [record(1, cr.BASE_REVISION_ID, SRC, [upd(mass_g=912000)], g1), record(2, cr.revision_id(1), SRC, c2, g2)]


# ---------------------------------------------------------------- ids and R0000
def test_revision_ids():
    assert cr.BASE_REVISION_ID == 'BALTIMORE-PIPE-V1-1@R0000' and cr.revision_id(12) == 'BALTIMORE-PIPE-V1-1@R0012'
    assert cr.parse_sequence('BALTIMORE-PIPE-V1-1@R0012') == 12
    for bad in ('BALTIMORE-PIPE-V1-1@R12', 'X@R0001', '', None, 'BALTIMORE-PIPE-V1-1@R00001'):
        with pytest.raises(ValueError):
            cr.parse_sequence(bad)
    with pytest.raises(ValueError):
        cr.revision_id(-1)


def test_base_hash_stable_and_matches_registry():
    assert cr.content_sha256(base()) == cr.content_sha256(base()) == BASE_SHA
    g = base()
    assert len(g) == 31 and sum(x['bundle_count'] for x in g) == 1076
    first = g[0]
    assert first['bundle_ids'][:2] == ['PIPE-R002-B0001', 'PIPE-R002-B0002'] and first['next_bundle_index'] == 161
    assert first['origin'] == 'WORKBOOK' and first['bundle_overrides'] == {} and first['source_row'] == 2


def test_base_units_match_registry_and_model():
    view = cr.replay(REG, [])[0]
    assert view['revision_id'] == cr.BASE_REVISION_ID and view['parent_revision_id'] is None and view['content_sha256'] == BASE_SHA
    units, legacy = cr.derive_units(view), pipe_registry.units()
    assert len(units) == len(legacy) == 1076
    for u, l in zip(units, legacy):
        for k in ('id', 'mass_g', 'dimensions_um', 'length_mm', 'width_mm', 'height_mm', 'name', 'kind', 'requirement'):
            assert u[k] == l[k]
        s, ls = u['source_ref'], l['source_ref']
        assert {k: s[k] for k in ls} == ls
        assert (s['revision_id'], s['confirmation']) == (cr.BASE_REVISION_ID, 'WORKBOOK')
        CargoUnit.model_validate(u)


# ---------------------------------------------------------------- change types
def test_update_group_fields_exact_and_effect():
    s = {'pieces_per_bundle': 10000, 'dimensions_um': [10 ** 9, 1, 123456789], 'mass_g': 10 ** 12,
         'outside_diameter_mm': '123456.7890', 'wall_thickness_mm': '0.0001', 'dimension_warning': True}
    new, delta, effect = apply([upd(**s)])
    g = gs(new, G2)
    assert all(g[k] == v for k, v in s.items()) and g['bundle_count'] == 160
    assert set(delta[G2]) == set(s) and effect['added_bundle_ids'] == effect['removed_bundle_ids'] == []
    assert len(effect['changed_bundle_ids']) == 160 and effect['summaries'][0]['index'] == 0
    assert gs(new, 'Sheet1-R003') == gs(base(), 'Sheet1-R003')


def test_bundle_count_decrease_drops_highest_and_never_reissues():
    new, _, effect = apply([upd(bundle_count=150)])
    g = gs(new, G2)
    assert g['bundle_count'] == 150 and g['bundle_ids'][-1] == 'PIPE-R002-B0150'
    assert effect['removed_bundle_ids'] == [f'PIPE-R002-B{i:04d}' for i in range(151, 161)]
    new2, _, effect2 = apply([upd(bundle_count=155)], new, rev=2)
    g2 = gs(new2, G2)
    assert effect2['added_bundle_ids'] == [f'PIPE-R002-B{i:04d}' for i in range(161, 166)]
    assert g2['bundle_ids'][150:] == effect2['added_bundle_ids'] and g2['next_bundle_index'] == 166
    assert 'PIPE-R002-B0151' not in g2['bundle_ids']


def test_decrease_then_increase_in_one_batch_issues_new_ids():
    new, _, effect = apply([upd(bundle_count=158), upd(bundle_count=160)])
    ids = gs(new, G2)['bundle_ids']
    assert ids[-2:] == ['PIPE-R002-B0161', 'PIPE-R002-B0162'] and 'PIPE-R002-B0159' not in ids
    assert effect['added_bundle_ids'] == ['PIPE-R002-B0161', 'PIPE-R002-B0162']
    assert effect['removed_bundle_ids'] == ['PIPE-R002-B0159', 'PIPE-R002-B0160']


def test_bundle_count_zero_withdraws_group_and_it_can_return():
    new, _, effect = apply([upd(bundle_count=0)])
    g = gs(new, G2)
    assert g['bundle_count'] == 0 and g['bundle_ids'] == [] and len(effect['removed_bundle_ids']) == 160
    assert len(cr.derive_units(_view(new))) == 1076 - 160
    back, _, effect2 = apply([upd(bundle_count=2)], new, rev=2)
    assert effect2['added_bundle_ids'] == ['PIPE-R002-B0161', 'PIPE-R002-B0162']


def test_add_group_ids_and_defaults():
    new, delta, effect = apply([add(), add(bundle_count=1, mass_g=7)])
    a1, a2 = new[-2], new[-1]
    assert (a1['group_id'], a2['group_id']) == ('ADD-001', 'ADD-002') and len(new) == 33
    assert a1['bundle_ids'] == ['PIPE-A001-B0001', 'PIPE-A001-B0002', 'PIPE-A001-B0003'] and a2['bundle_ids'] == ['PIPE-A002-B0001']
    assert a1['origin'] == 'ADDED' and a1['source_row'] is None and a1['issue_codes'] == []
    assert a1['source_line_t'] is a1['source_cbm_m3'] is a1['envelope_cbm_m3'] is None and a1['next_bundle_index'] == 4
    assert set(delta['ADD-001']) == set(cr.GROUP_FIELDS)
    assert effect['added_bundle_ids'] == a1['bundle_ids'] + a2['bundle_ids']
    # later change in same batch can see the new group; withdrawn added groups still count for numbering
    new2, _, _ = apply([add(), upd('ADD-001', bundle_count=0)])
    new3, _, _ = apply([add()], new2, rev=2)
    assert new3[-1]['group_id'] == 'ADD-002'


def test_bundle_override_effective_values_and_provenance():
    bid = 'PIPE-R002-B0005'
    new, delta, effect = apply([ovr(bid, mass_g=905000), ovr(bid, dimensions_um=[6400000, 300000, 290000])])
    g = gs(new, G2)
    assert g['bundle_overrides'] == {bid: {'mass_g': 905000, 'dimensions_um': [6400000, 300000, 290000]}}
    assert g['mass_g'] == 911400 and effect['changed_bundle_ids'] == [bid]
    units = {u['id']: u for u in cr.derive_units(_view(new, delta))}
    u = units[bid]
    assert (u['mass_g'], u['dimensions_um'], u['length_mm'], u['width_mm'], u['height_mm']) == (905000, [6400000, 300000, 290000], 6400, 300, 290)
    assert units['PIPE-R002-B0006']['mass_g'] == 911400
    assert set(delta['__bundles__'][bid]) == {'mass_g', 'dimensions_um'}


def test_override_dropped_when_bundle_removed_and_group_update_keeps_override_winning():
    bid = 'PIPE-R002-B0160'
    new, delta, _ = apply([ovr(bid, mass_g=1), upd(bundle_count=159)])
    assert gs(new, G2)['bundle_overrides'] == {}
    prov = cr.apply_provenance(cr.base_provenance(base()), delta, new)
    assert bid not in prov['__bundles__']
    new, delta, _ = apply([ovr('PIPE-R002-B0001', mass_g=42, conf='UNVERIFIED'), upd(mass_g=5000)])
    units = {u['id']: u for u in cr.derive_units(_view(new, delta))}
    assert units['PIPE-R002-B0001']['mass_g'] == 42 and units['PIPE-R002-B0002']['mass_g'] == 5000
    assert units['PIPE-R002-B0001']['source_ref']['confirmation'] == 'UNVERIFIED'
    assert units['PIPE-R002-B0002']['source_ref']['confirmation'] == 'CONFIRMED'


def test_changes_apply_in_order():
    new, _, _ = apply([upd(mass_g=100), upd(mass_g=200), add(), upd('ADD-001', bundle_count=5), ovr('PIPE-A001-B0005', mass_g=9)])
    assert gs(new, G2)['mass_g'] == 200 and gs(new, 'ADD-001')['bundle_count'] == 5
    assert gs(new, 'ADD-001')['bundle_overrides'] == {'PIPE-A001-B0005': {'mass_g': 9}}
    # a later change cannot see a group that is only added afterwards
    e = errs([upd('ADD-001', mass_g=5), add()])
    assert e[0]['index'] == 0 and e[0]['field'] == 'group_id'
    # override of a bundle dropped earlier in the same batch is rejected
    e = errs([upd(bundle_count=10), ovr('PIPE-R002-B0011', mass_g=5)])
    assert [(x['index'], x['field']) for x in e] == [(1, 'bundle_id')]


def _view(groups, delta=None, rev='BALTIMORE-PIPE-V1-1@R0001'):
    prov = cr.apply_provenance(cr.base_provenance(base()), delta or {'__bundles__': {}}, groups)
    return {'revision_id': rev, 'groups': groups, 'provenance': prov}


# ---------------------------------------------------------------- provenance
def test_provenance_fields_and_unit_refs():
    changes = [upd(mass_g=912000, conf='UNVERIFIED'), upd('Sheet1-R003', conf='CONFIRMED', pieces_per_bundle=9),
               ovr('PIPE-R004-B0001', conf='CONFIRMED', mass_g=1111)]
    src = {'kind': 'USER', 'reference': '  tay  ', 'received_date': '2026-11-02'}
    new, delta, _ = apply(changes, source=src, rev=3)
    rev3 = cr.revision_id(3)
    prov = cr.apply_provenance(cr.base_provenance(base()), delta, new)
    stamp = prov[G2]['mass_g']
    assert stamp == {'revision_id': rev3, 'confirmation': 'UNVERIFIED',
                     'source': {'kind': 'USER', 'reference': 'tay', 'received_date': '2026-11-02', 'note': ''}}
    assert prov[G2]['pieces_per_bundle'] == {'revision_id': cr.BASE_REVISION_ID, 'source': None, 'confirmation': 'WORKBOOK'}
    assert prov['Sheet1-R003']['pieces_per_bundle']['confirmation'] == 'CONFIRMED'
    assert prov['__bundles__']['PIPE-R004-B0001']['mass_g']['revision_id'] == rev3
    units = {u['id']: u['source_ref'] for u in cr.derive_units({'groups': new, 'provenance': prov, 'revision_id': rev3})}
    assert (units['PIPE-R002-B0001']['revision_id'], units['PIPE-R002-B0001']['confirmation']) == (rev3, 'UNVERIFIED')
    assert (units['PIPE-R003-B0001']['revision_id'], units['PIPE-R003-B0001']['confirmation']) == (rev3, 'CONFIRMED')
    assert (units['PIPE-R004-B0001']['revision_id'], units['PIPE-R004-B0001']['confirmation']) == (rev3, 'CONFIRMED')
    assert (units['PIPE-R004-B0002']['revision_id'], units['PIPE-R004-B0002']['confirmation']) == (cr.BASE_REVISION_ID, 'WORKBOOK')
    assert units['PIPE-R005-B0001']['confirmation'] == 'WORKBOOK'


def test_unverified_wins_and_highest_revision_wins():
    v = cr.replay(REG, two_revisions())
    assert [x['revision_id'] for x in v] == [cr.revision_id(i) for i in range(3)]
    u = {x['id']: x['source_ref'] for x in cr.derive_units(v[2])}
    # B0002 mass override (R0002, CONFIRMED); dimensions come from workbook, group mass R0001 not used (override wins)
    assert (u['PIPE-R002-B0002']['revision_id'], u['PIPE-R002-B0002']['confirmation']) == (cr.revision_id(2), 'CONFIRMED')
    assert (u['PIPE-R002-B0003']['revision_id'], u['PIPE-R002-B0003']['confirmation']) == (cr.revision_id(1), 'CONFIRMED')
    # added group is UNVERIFIED at R0002 and has no source_row
    assert (u['PIPE-A001-B0001']['revision_id'], u['PIPE-A001-B0001']['confirmation'], u['PIPE-A001-B0001']['source_row']) == (cr.revision_id(2), 'UNVERIFIED', None)
    assert v[1]['source']['reference'] == SRC['reference'] and v[2]['parent_revision_id'] == cr.revision_id(1)
    assert v[2]['provenance']['__bundles__']['PIPE-R002-B0002']['mass_g']['source']['kind'] == 'FACTORY'


def test_bundle_added_by_count_increase_carries_creating_revision():
    new, delta, _ = apply([upd(conf='UNVERIFIED', bundle_count=162)], rev=2)
    units = {u['id']: u['source_ref'] for u in cr.derive_units(_view(new, delta, cr.revision_id(2)))}
    assert (units['PIPE-R002-B0161']['revision_id'], units['PIPE-R002-B0161']['confirmation']) == (cr.revision_id(2), 'UNVERIFIED')
    assert units['PIPE-R002-B0160']['confirmation'] == 'WORKBOOK'


def test_added_unit_is_valid_cargo_unit_with_a_prefix_name():
    new, delta, _ = apply([add()])
    units = cr.derive_units(_view(new, delta))
    added = [u for u in units if u['id'].startswith('PIPE-A001')]
    assert len(added) == 3 and added[0]['name'] == 'Ống thép nhóm A001'
    for u in added:
        CargoUnit.model_validate(u)


# ---------------------------------------------------------------- dimension_warning
def test_dimension_warning_off_requires_confirmation():
    assert gs(base(), G22)['dimension_warning'] is True
    e = one([upd(G22, conf='UNVERIFIED', dimension_warning=False)])
    assert (e['index'], e['field']) == (0, 'set.dimension_warning')
    new, delta, _ = apply([upd(G22, conf='CONFIRMED', dimension_warning=False)])
    assert gs(new, G22)['dimension_warning'] is False
    assert delta[G22]['dimension_warning']['confirmation'] == 'CONFIRMED'
    # false -> true is always allowed, and true -> true unverified too
    apply([upd(G2, conf='UNVERIFIED', dimension_warning=True)])
    apply([upd(G22, conf='UNVERIFIED', dimension_warning=True)])
    # order matters: turning on then off unverified is rejected
    assert errs([upd(G2, conf='UNVERIFIED', dimension_warning=True), upd(G2, conf='UNVERIFIED', dimension_warning=False)])[0]['index'] == 1


# ---------------------------------------------------------------- D3 limits
def test_batch_level_change_count_limits():
    e = errs([])
    assert e == [{'index': None, 'field': 'changes', 'message': e[0]['message']}] and 'ít nhất' in e[0]['message']
    e = errs([upd(mass_g=1)] * 501)
    assert len(e) == 1 and (e[0]['index'], e[0]['field']) == (None, 'changes') and '500' in e[0]['message']
    assert errs([upd(mass_g=1)] * 500) == []
    assert errs('x')[0]['field'] == 'changes'


def test_payload_limit():
    assert cr.check_payload_size(cr.MAX_PAYLOAD_BYTES) == []
    e = cr.check_payload_size(cr.MAX_PAYLOAD_BYTES + 1)
    assert e[0]['index'] is None and e[0]['field'] == 'payload' and '1 MiB' in e[0]['message']


def test_group_count_limit():
    assert errs([add(bundle_count=1)] * 169) == []
    e = errs([add(bundle_count=1)] * 170)  # 31 + 170 = 201
    assert (e[0]['index'], e[0]['field']) == (None, 'changes') and '200' in e[0]['message'] and len(e) == 1


def test_total_and_group_bundle_limits():
    ok, _, _ = apply([add(bundle_count=924)])  # 1076 + 924 = 2000
    assert sum(len(g['bundle_ids']) for g in ok) == 2000
    e = errs([add(bundle_count=925)])
    assert len(e) == 1 and (e[0]['index'], e[0]['field']) == (None, 'changes') and '2000' in e[0]['message']
    assert errs([add(bundle_count=1000), upd(bundle_count=0)]) == []  # final state counts
    for ch, field in ((upd(bundle_count=2001), 'set.bundle_count'), (add(bundle_count=2001), 'group.bundle_count')):
        e = one([ch])
        assert (e['index'], e['field']) == (0, field) and '2000' in e['message']
    assert one([upd(bundle_count=-1)])['field'] == 'set.bundle_count'
    assert one([add(bundle_count=0)])['field'] == 'group.bundle_count'
    assert errs([upd(bundle_count=2000)])[0]['field'] == 'changes'  # 2000 in one group + the rest exceeds the total


@pytest.mark.parametrize('field,bad,good', [
    ('pieces_per_bundle', [0, 10001, -3], 10000),
    ('mass_g', [0, 10 ** 12 + 1], 10 ** 12),
])
def test_scalar_limits(field, bad, good):
    for b in bad:
        e = one([upd(**{field: b})])
        assert (e['index'], e['field']) == (0, f'set.{field}')
    new, _, _ = apply([upd(**{field: good})])
    assert gs(new, G2)[field] == good


def test_dimension_limits_with_element_index():
    for pos in range(3):
        for bad in (0, 10 ** 9 + 1):
            dims = [5, 5, 5]
            dims[pos] = bad
            e = one([upd(dimensions_um=dims)])
            assert (e['index'], e['field']) == (0, f'set.dimensions_um.{pos}')
    for bad in ([1, 2], [1, 2, 3, 4], 5, 'abc'):
        assert one([upd(dimensions_um=bad)])['field'] == 'set.dimensions_um'
    new, _, _ = apply([upd(dimensions_um=[10 ** 9, 1, 999999999])])
    assert gs(new, G2)['dimensions_um'] == [10 ** 9, 1, 999999999]
    assert one([ovr('PIPE-R002-B0001', mass_g=0)])['field'] == 'set.mass_g'
    assert one([ovr('PIPE-R002-B0001', dimensions_um=[1, 0, 1])])['field'] == 'set.dimensions_um.1'
    apply([ovr('PIPE-R002-B0001', mass_g=10 ** 12, dimensions_um=[10 ** 9] * 3)])


def test_bool_float_and_string_rejected_for_ints():
    for field in ('bundle_count', 'pieces_per_bundle', 'mass_g'):
        for bad in (True, False, 5.0, 5.5, '5', None):
            e = one([upd(**{field: bad})])
            assert (e['index'], e['field']) == (0, f'set.{field}') and 'số nguyên' in e['message']
    assert one([upd(dimensions_um=[1.0, 2, 3])])['field'] == 'set.dimensions_um.0'
    assert one([upd(dimensions_um=[1, True, 3])])['field'] == 'set.dimensions_um.1'
    assert one([ovr('PIPE-R002-B0001', mass_g=1.5)])['field'] == 'set.mass_g'
    assert one([add(pieces_per_bundle=True)])['field'] == 'group.pieces_per_bundle'


def test_decimal_strings_and_warning_type():
    for field in ('outside_diameter_mm', 'wall_thickness_mm'):
        for bad in ('0', '0.0', '-1', '1e3', '1234567', '1.23456', '', ' 1', 'a', 12, 1.5, None):
            assert one([upd(**{field: bad})])['field'] == f'set.{field}', bad
        for good in ('0.0001', '999999.9999', '5'):
            apply([upd(**{field: good})])
    assert one([upd(dimension_warning=1)])['field'] == 'set.dimension_warning'
    assert one([upd(dimension_warning='false')])['field'] == 'set.dimension_warning'


def test_source_validation():
    def src(**o):
        s = dict(SRC)
        s.update(o)
        return s
    cases = [({'kind': 'ROBOT'}, 'kind'), ({'kind': None}, 'kind'), ({'reference': ''}, 'reference'),
             ({'reference': '   '}, 'reference'), ({'reference': 'x' * 201}, 'reference'), ({'reference': 5}, 'reference'),
             ({'received_date': '2026-02-30'}, 'received_date'), ({'received_date': '04-11-2026'}, 'received_date'),
             ({'received_date': '2026-11-04T00:00'}, 'received_date'), ({'received_date': 20261104}, 'received_date'),
             ({'note': 'n' * 501}, 'note'), ({'note': 5}, 'note')]
    for over, field in cases:
        e = errs([upd(mass_g=1)], source=src(**over))
        assert [(x['index'], x['field']) for x in e] == [(None, f'source.{field}')], over
        assert e[0]['message']
    assert errs([upd(mass_g=1)], source=src(extra=1))[0]['field'] == 'source.extra'
    assert errs([upd(mass_g=1)], source='x')[0]['field'] == 'source'
    assert errs([upd(mass_g=1)], source={})[0]['index'] is None
    for kind in cr.SOURCE_KINDS:
        assert errs([upd(mass_g=1)], source=src(kind=kind)) == []
    assert errs([upd(mass_g=1)], source=src(reference='x' * 200, note='n' * 500, received_date='2024-02-29')) == []
    s = {k: v for k, v in SRC.items() if k != 'note'}
    new, delta, _ = apply([upd(mass_g=1)], source=s)
    assert delta[G2]['mass_g']['source']['note'] == ''


def test_structure_errors_and_unknown_targets():
    e = one([upd('NOPE', mass_g=5)])
    assert (e['index'], e['field']) == (0, 'group_id') and 'NOPE' in e['message']
    for bid in ('PIPE-R002-B0161', 'PIPE-X-B1', 5, None):
        c = ovr('PIPE-R002-B0001', mass_g=5)
        c['bundle_id'] = bid
        assert one([c])['field'] == 'bundle_id'
    assert one([upd(**{})])['field'] == 'set'
    assert one([ovr('PIPE-R002-B0001')])['field'] == 'set'
    assert one([upd(bogus=1)])['field'] == 'set.bogus'
    assert one([ovr('PIPE-R002-B0001', bundle_count=3)])['field'] == 'set.bundle_count'
    assert one([ovr('PIPE-R002-B0001', dimension_warning=True)])['field'] == 'set.dimension_warning'
    assert one([{**upd(mass_g=1), 'extra': 1}])['field'] == 'extra'
    assert one([{'type': 'NOPE'}])['field'] == 'type'
    assert one([{'group_id': G2, 'set': {'mass_g': 1}}])['field'] == 'type'
    assert one(['x'])['field'] == 'change'
    c = upd(mass_g=1)
    del c['group_id']
    assert one([c])['field'] == 'group_id'
    c = upd(mass_g=1)
    c['confirmation'] = 'MAYBE'
    assert one([c])['field'] == 'confirmation'
    del c['confirmation']
    assert one([c])['field'] == 'confirmation'
    g = add()
    del g['group']['wall_thickness_mm']
    assert one([g])['field'] == 'group.wall_thickness_mm'
    g = add()
    g['group']['extra'] = 1
    assert one([g])['field'] == 'group.extra'
    g = add()
    g['group'] = {}
    assert {x['field'] for x in errs([g])} >= {'group', 'group.mass_g'}


def test_all_errors_collected_with_positions():
    e = errs([upd(mass_g=0), upd(mass_g=5), upd('NOPE', pieces_per_bundle=0), ovr('PIPE-R002-B0001', mass_g=True)])
    assert [(x['index'], x['field']) for x in e] == [(0, 'set.mass_g'), (2, 'group_id'), (2, 'set.pieces_per_bundle'), (3, 'set.mass_g')]
    assert all(set(x) == {'index', 'field', 'message'} for x in e)


def test_apply_batch_raises_on_invalid():
    with pytest.raises(ValueError) as ei:
        apply([upd(mass_g=0)])
    assert ei.value.errors[0]['field'] == 'set.mass_g'
    with pytest.raises(ValueError):
        cr.apply_batch(base(), SRC, [upd(mass_g=1)], 'bad')


def test_exact_integers_preserved():
    new, _, _ = apply([upd(mass_g=911401, dimensions_um=[6401001, 337601, 295401])])
    g = gs(new, G2)
    assert (g['mass_g'], g['dimensions_um']) == (911401, [6401001, 337601, 295401])
    assert type(g['mass_g']) is int and all(type(x) is int for x in g['dimensions_um'])
    u = cr.derive_units(_view(new))[0]
    assert (u['length_mm'], u['width_mm'], u['height_mm']) == (6402, 338, 296)  # ceil(µm / 1000)


# ---------------------------------------------------------------- replay
def test_replay_two_revisions_matches_incremental_apply():
    recs = two_revisions()
    views = cr.replay(REG, recs)
    assert len(views) == 3
    assert [v['content_sha256'] for v in views] == [BASE_SHA, recs[0]['content_sha256'], recs[1]['content_sha256']]
    assert views[0]['groups'] == base() and views[1]['created_utc'] == '2026-11-04T00:00:00Z'
    assert gs(views[1]['groups'], G2)['mass_g'] == 912000 and gs(views[0]['groups'], G2)['mass_g'] == 911400
    assert gs(views[2]['groups'], 'ADD-001')['bundle_count'] == 3
    assert views[2]['changes'] == recs[1]['changes'] and views[0]['provenance'] == cr.base_provenance(base())
    assert views[1]['provenance'][G2]['mass_g']['revision_id'] == cr.revision_id(1)
    assert cr.replay(REG, []) [0]['groups'] == base()


def test_replay_detects_tampering():
    def bad(mutate, expect):
        recs = copy.deepcopy(two_revisions())
        mutate(recs)
        with pytest.raises(cr.RevisionIntegrityError) as ei:
            cr.replay(REG, recs)
        assert ei.value.revision_id == expect and ei.value.message
    bad(lambda r: r[0].update(content_sha256='0' * 64), cr.revision_id(1))
    bad(lambda r: r[1].update(content_sha256=r[0]['content_sha256']), cr.revision_id(2))
    bad(lambda r: r[0]['changes'][0]['set'].update(mass_g=912001), cr.revision_id(1))
    bad(lambda r: r[1]['changes'][1]['set'].update(mass_g=900001), cr.revision_id(2))
    bad(lambda r: r[1]['changes'].pop(), cr.revision_id(2))
    bad(lambda r: r[0]['changes'][0].update(group_id='NOPE'), cr.revision_id(1))  # replay no longer valid
    bad(lambda r: r[1].update(parent_revision_id=cr.BASE_REVISION_ID), cr.revision_id(2))
    bad(lambda r: r[1].update(revision_id=cr.revision_id(3)), cr.revision_id(3))
    bad(lambda r: r.reverse(), cr.revision_id(2))
    bad(lambda r: r[0].update(source={'kind': 'X', 'reference': 'a', 'received_date': '2026-11-01'}), cr.revision_id(1))


# ---------------------------------------------------------------- diff_units
def test_diff_units():
    recs = two_revisions()
    v = cr.replay(REG, recs)
    old, new = cr.derive_units(v[0]), cr.derive_units(v[2])
    d = cr.diff_units(old, new)
    assert d['added'] == ['PIPE-A001-B0001', 'PIPE-A001-B0002', 'PIPE-A001-B0003'] and d['removed'] == []
    assert len(d['changed']) == 160 and 'PIPE-R003-B0001' not in d['changed']
    d2 = cr.diff_units(new, cr.derive_units(cr.replay(REG, recs[:1])[1]))
    assert d2['removed'] == d['added'] and d2['added'] == []
    only_req = copy.deepcopy(old)
    only_req[0]['requirement'] = 'required'
    assert cr.diff_units(old, only_req) == {'added': [], 'removed': [], 'changed': []}
    only_ref = copy.deepcopy(old)
    only_ref[1]['source_ref']['confirmation'] = 'CONFIRMED'
    assert cr.diff_units(old, only_ref)['changed'] == [old[1]['id']]
    assert cr.diff_units(old, []) == {'added': [], 'removed': [u['id'] for u in old], 'changed': []}


# ---------------------------------------------------------------- purity
def test_inputs_never_mutated():
    groups, source = base(), copy.deepcopy(SRC)
    changes = [upd(bundle_count=150, dimensions_um=[1, 2, 3]), add(), ovr('PIPE-R003-B0001', dimensions_um=[4, 5, 6]),
               ovr('PIPE-R002-B0001', mass_g=3)]
    snap = (copy.deepcopy(groups), copy.deepcopy(source), copy.deepcopy(changes))
    cr.validate_batch(groups, source, changes)
    new, delta, effect = cr.apply_batch(groups, source, changes, cr.revision_id(1))
    assert (groups, source, changes) == snap and new is not groups
    new[0]['bundle_ids'].append('X')
    new[1]['dimensions_um'][0] = 99
    delta[G2]['mass_g' if 'mass_g' in delta.get(G2, {}) else 'bundle_count']['source']['kind'] = 'OTHER'
    assert (groups, source, changes) == snap
    # stored dimension lists are copies of the change input
    assert gs(new, 'Sheet1-R003')['bundle_overrides']['PIPE-R003-B0001']['dimensions_um'] is not changes[2]['set']['dimensions_um']
    recs = two_revisions()
    before = copy.deepcopy(recs)
    views = cr.replay(REG, recs)
    assert recs == before
    views[2]['groups'][0]['mass_g'] = -1
    views[2]['changes'].clear()
    assert recs == before
    prov = cr.base_provenance(groups)
    snap_p = copy.deepcopy(prov)
    cr.apply_provenance(prov, delta, new)
    assert prov == snap_p
    units = cr.derive_units(views[0])
    units2 = cr.derive_units(views[0])
    units[0]['dimensions_um'][0] = -1
    assert units2[0]['dimensions_um'][0] == 6401000 and REG['groups'][0]['dimensions_um'][0] == 6401000
