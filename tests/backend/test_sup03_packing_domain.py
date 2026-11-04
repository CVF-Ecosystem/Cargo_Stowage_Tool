import copy
import json
import time

import pytest
from app.adapters.pipe_registry import REGISTRY
from app.domain import cargo_revisions as cr
from app.domain import packing

VIEW = cr.replay(REGISTRY, [])[0]
L = 1_000_000


def sec(pieces, od, w, h, wall='5', warn=False, length=L):
    return packing.pack_section(pieces, od, wall, [length, w, h], warn)


def codes(p):
    return [r['code'] for r in p['reasons']]


def walk(x):
    """Yield every leaf of nested dict/list data."""
    if isinstance(x, dict):
        for k, v in x.items():
            assert isinstance(k, str)
            yield from walk(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from walk(v)
    else:
        yield x


def assert_inside(p):
    od, (w, h) = p['od_um'], p['section_um']
    for y, z in p['pipe_centres_um']:
        assert 2 * y - od >= 0 and 2 * y + od <= 2 * w and 2 * z - od >= 0 and 2 * z + od <= 2 * h


def assert_no_overlap_beyond_rounding(p):
    od = p['od_um']
    cs = p['pipe_centres_um']
    for i, (y1, z1) in enumerate(cs):
        for y2, z2 in cs[i + 1:]:
            # exact: distance^2 >= (od-1)^2, i.e. overlap strictly below 1 µm (HEX rounding allowance)
            assert (y1 - y2) ** 2 + (z1 - z2) ** 2 >= (od - 1) ** 2


# ---------------------------------------------------------------- mm_to_um
@pytest.mark.parametrize('s,um', [('42.2', 42200), ('42', 42000), ('42.2000', 42200), ('0.001', 1), ('219.1', 219100),
                                  ('10.001', 10001), ('73', 73000), ('999999.999', 999999999), ('0.1', 100)])
def test_mm_to_um_valid(s, um):
    got = packing.mm_to_um(s)
    assert got == um and type(got) is int


@pytest.mark.parametrize('s', ['', 'abc', '0', '0.000', '-1', '42.2005', None, 42.2, 42, ' 42', '42 ', '42.', '.5', '1e3',
                               '42.20000', '1234567', '42\n', '4,2', '٤٢', '+5', '0.0001'])
def test_mm_to_um_invalid(s):
    assert packing.mm_to_um(s) is None


# ---------------------------------------------------------------- layouts
def test_rect_case_exact_centres():
    p = sec(6, '10', 30000, 20000)  # 3 x 2 grid of 10 mm pipes exactly
    assert p['status'] == 'DETAILED' and p['layout'] == 'RECT' and (p['columns'], p['rows']) == (3, 2)
    assert p['pipe_centres_um'] == [[5000, 5000], [15000, 5000], [25000, 5000], [5000, 15000], [15000, 15000], [25000, 15000]]
    assert p['pieces_placed'] == p['pieces_source'] == 6 and p['max_fit'] == 6
    assert p['slack_um'] == [0, 0] and p['basis'] == 'DERIVED'
    assert p['checks'] == {'count': True, 'od_fit': True, 'envelope_fit': True, 'slack_loose': False}
    assert p['reasons'] == [] and p['od_um'] == 10000 and p['wall_thickness_um'] == 5000
    assert p['length_um'] == L and p['section_um'] == [30000, 20000]


def test_rect_partial_last_row_and_columns_used():
    p = sec(4, '10', 30000, 30000)
    assert (p['layout'], p['columns'], p['rows']) == ('RECT', 3, 2) and p['pieces_placed'] == 4
    assert p['pipe_centres_um'][3] == [5000, 15000]
    assert p['slack_um'] == [0, 10000]
    p = sec(2, '10', 100000, 10000)
    assert (p['columns'], p['rows']) == (2, 1)


def test_hex_case_rect_insufficient_hex_fits():
    p = sec(5, '100', 250000, 280000)  # rect 2x2=4, hex 2+2+2=6
    assert p['status'] == 'DETAILED' and p['layout'] == 'HEX' and (p['columns'], p['rows']) == (2, 3)
    assert p['pipe_centres_um'] == [[50000, 50000], [150000, 50000], [100000, 136602], [200000, 136602], [50000, 223204]]
    assert p['max_fit'] == 6 and p['slack_um'] == [0, 6796]
    assert p['checks']['envelope_fit'] and p['checks']['count']
    assert_inside(p)
    assert_no_overlap_beyond_rounding(p)
    full = sec(6, '100', 250000, 280000)
    assert full['layout'] == 'HEX' and full['pieces_placed'] == 6
    assert_inside(full)
    assert_no_overlap_beyond_rounding(full)


def test_pieces_do_not_fit_reports_max_fit():
    p = sec(7, '100', 250000, 280000)  # max is hex 6
    assert p['status'] == 'ENVELOPE_ONLY' and codes(p) == ['PIECES_DO_NOT_FIT']
    assert p['max_fit'] == 6 and ' 6 ' in p['reasons'][0]['message']
    assert p['reasons'][0]['message'].endswith('Kiểm lại OD, số ống mỗi bó hoặc kích thước bó trong revision.')
    assert p['layout'] is None and (p['columns'], p['rows'], p['pieces_placed']) == (0, 0, 0)
    assert p['pipe_centres_um'] == [] and p['slack_um'] is None and p['pieces_source'] == 7
    assert p['checks'] == {'count': False, 'od_fit': True, 'envelope_fit': False, 'slack_loose': False}
    r = sec(5, '100', 200000, 200000)  # rect 4 beats hex 3
    assert codes(r) == ['PIECES_DO_NOT_FIT'] and r['max_fit'] == 4


@pytest.mark.parametrize('od', ['', 'abc', '0', '-1', '42.2005', None, 42.2, '1e2'])
def test_od_missing_or_invalid(od):
    p = packing.pack_section(5, od, '5', [L, 100000, 100000], False)
    assert p['status'] == 'ENVELOPE_ONLY' and codes(p) == ['OD_MISSING'] and p['od_um'] is None
    assert p['reasons'][0]['message'].endswith('Kiểm lại OD, số ống mỗi bó hoặc kích thước bó trong revision.')
    assert p['checks']['od_fit'] is False and p['layout'] is None and p['max_fit'] == 0


@pytest.mark.parametrize('w,h', [(30000, 100000), (100000, 30000), (30000, 30000)])
def test_od_exceeds_section(w, h):
    p = sec(1, '40', w, h)
    assert p['status'] == 'ENVELOPE_ONLY' and codes(p) == ['OD_EXCEEDS_SECTION']
    assert p['checks']['od_fit'] is False and p['pipe_centres_um'] == [] and p['max_fit'] == 0
    assert p['od_um'] == 40000 and p['section_um'] == [w, h]


def test_odd_um_od_envelope_fit_and_conservative_count():
    p = sec(4, '10.001', 20003, 20003)  # OD = 10001 µm (odd), centres at ceil(OD/2) = 5001
    assert p['status'] == 'DETAILED' and p['od_um'] == 10001
    assert p['pipe_centres_um'] == [[5001, 5001], [15002, 5001], [5001, 15002], [15002, 15002]]
    assert p['checks']['envelope_fit'] is True and p['slack_um'] == [0, 0]
    assert_inside(p)
    # 20002 = exactly 2*OD is one µm short for the ceil-based centre offset: not claimed as fitting
    q = sec(4, '10.001', 20002, 20002)
    assert q['status'] == 'ENVELOPE_ONLY' and codes(q) == ['PIECES_DO_NOT_FIT'] and q['max_fit'] < 4


@pytest.mark.parametrize('od', ['10.001', '10.003', '33.333', '7.001', '100.007'])
def test_odd_od_every_layout_stays_inside(od):
    um = packing.mm_to_um(od)
    for w in (um * 3 + 1, um * 3 + 2, um * 5 + 7):
        for h in (um * 2 + 1, um * 4 + 3, um * 6):
            cap = sec(10_000, od, w, h)['max_fit']
            for n in {1, 2, cap // 2 or 1, cap or 1}:
                p = sec(n, od, w, h)
                if p['status'] == 'DETAILED':
                    assert_inside(p)
                    assert p['checks']['envelope_fit'] and p['pieces_placed'] == n
                    assert all(s >= 0 for s in p['slack_um'])
                else:
                    assert n > cap


# ---------------------------------------------------------------- reasons
def test_envelope_loose_is_informational():
    p = sec(2, '10', 100000, 10000)  # width slack 80 mm >= OD
    assert p['status'] == 'DETAILED' and codes(p) == ['ENVELOPE_LOOSE'] and p['checks']['slack_loose'] is True
    assert p['slack_um'] == [80000, 0]
    t = sec(2, '10', 20000, 100000)
    assert codes(t) == ['ENVELOPE_LOOSE'] and t['slack_um'] == [0, 90000]
    tight = sec(2, '10', 25000, 15000)  # slack 5 mm each, below OD
    assert tight['status'] == 'DETAILED' and tight['reasons'] == [] and tight['checks']['slack_loose'] is False


def test_source_warning_retained_and_does_not_change_status():
    clean = sec(6, '10', 30000, 20000)
    warned = sec(6, '10', 30000, 20000, warn=True)
    assert warned['status'] == 'DETAILED' and codes(warned) == ['SOURCE_WARNING']
    assert {k: v for k, v in warned.items() if k != 'reasons'} == {k: v for k, v in clean.items() if k != 'reasons'}
    both = sec(2, '10', 100000, 10000, warn=True)
    assert codes(both) == ['ENVELOPE_LOOSE', 'SOURCE_WARNING']
    bad = sec(99, '10', 30000, 20000, warn=True)
    assert bad['status'] == 'ENVELOPE_ONLY' and codes(bad) == ['PIECES_DO_NOT_FIT', 'SOURCE_WARNING']


@pytest.mark.parametrize('pieces,dims', [(0, [L, 1000, 1000]), (-3, [L, 1000, 1000]), (10_001, [L, 1000, 1000]),
                                         (True, [L, 1000, 1000]), (5.0, [L, 1000, 1000]), ('5', [L, 1000, 1000]),
                                         (None, [L, 1000, 1000]), (5, [L, 1000]), (5, [L, 1000, 1000, 1]),
                                         (5, [L, 0, 1000]), (5, [L, -1, 1000]), (5, [L, 1000.0, 1000]),
                                         (5, [L, True, 1000]), (5, None), (5, 'abc')])
def test_input_invalid(pieces, dims):
    p = packing.pack_section(pieces, '10', '1', dims, False)
    assert p['status'] == 'ENVELOPE_ONLY' and codes(p) == ['INPUT_INVALID']
    assert p['layout'] is None and p['pipe_centres_um'] == [] and p['slack_um'] is None
    assert all(type(x) is int for x in p['section_um']) and type(p['length_um']) is int
    assert type(p['pieces_source']) is int
    assert not any(isinstance(v, float) for v in walk(p))
    json.dumps(p, allow_nan=False)


def test_input_invalid_with_od_missing_lists_both_in_order():
    p = packing.pack_section(0, 'abc', '1', [L, 1000, 1000], True)
    assert codes(p) == ['INPUT_INVALID', 'OD_MISSING', 'SOURCE_WARNING']


def test_every_reason_code_has_a_case():
    seen = set()
    for p in (packing.pack_section(5, None, '1', [L, 1000, 1000], False),  # OD_MISSING
              sec(1, '40', 30000, 30000),  # OD_EXCEEDS_SECTION
              sec(99, '10', 30000, 20000),  # PIECES_DO_NOT_FIT
              packing.pack_section(0, '10', '1', [L, 1000, 1000], False),  # INPUT_INVALID
              sec(2, '10', 100000, 10000),  # ENVELOPE_LOOSE
              sec(6, '10', 30000, 20000, warn=True)):  # SOURCE_WARNING
        seen.update(codes(p))
        assert all(r['message'] and set(r) == {'code', 'message'} for r in p['reasons'])
    assert seen == {'OD_MISSING', 'OD_EXCEEDS_SECTION', 'PIECES_DO_NOT_FIT', 'INPUT_INVALID', 'ENVELOPE_LOOSE', 'SOURCE_WARNING'}


def test_wall_thickness_conversion_and_none():
    assert packing.pack_section(1, '10', '2.5', [L, 20000, 20000], False)['wall_thickness_um'] == 2500
    assert packing.pack_section(1, '10', 'x', [L, 20000, 20000], False)['wall_thickness_um'] is None
    assert packing.pack_section(1, '10', None, [L, 20000, 20000], False)['wall_thickness_um'] is None


def test_ten_thousand_pieces_fast_and_exact():
    t = time.perf_counter()
    p = sec(10_000, '1', 100_000, 100_000)
    assert time.perf_counter() - t < 2
    assert p['status'] == 'DETAILED' and p['pieces_placed'] == 10_000 and (p['columns'], p['rows']) == (100, 100)
    assert len(p['pipe_centres_um']) == 10_000 and p['slack_um'] == [0, 0]
    assert_inside(p)
    t = time.perf_counter()
    q = sec(10_000, '0.001', 10 ** 9, 10 ** 9)  # absurd capacity must not cost time or break the JSON number range
    assert time.perf_counter() - t < 2
    assert q['status'] == 'DETAILED' and q['max_fit'] <= 2 ** 53 - 1


# ---------------------------------------------------------------- purity
def test_no_floats_and_deterministic():
    cases = [sec(6, '10', 30000, 20000, warn=True), sec(5, '100', 250000, 280000), sec(7, '100', 250000, 280000),
             sec(4, '10.001', 20003, 20003), packing.pack_section(5, None, None, [L, 1, 1], False)]
    for p in cases:
        assert not any(isinstance(v, float) for v in walk(p))
        assert all(type(v) in (int, str, bool, type(None)) for v in walk(p))
        assert json.dumps(p) == json.dumps(copy.deepcopy(p))
    a, b = packing.pack_revision(VIEW), packing.pack_revision(VIEW)
    assert a == b and json.dumps(a) == json.dumps(b)
    assert not any(isinstance(v, float) for v in walk(a))
    assert all(type(v) in (int, str, bool, type(None)) for v in walk(a))
    json.dumps(a, allow_nan=False)


def test_inputs_not_mutated_and_output_not_aliased():
    view = copy.deepcopy(VIEW)
    view['groups'][0]['bundle_overrides'][view['groups'][0]['bundle_ids'][0]] = {'dimensions_um': [L, 500000, 500000]}
    before = copy.deepcopy(view)
    out = packing.pack_revision(view)
    assert view == before
    out['groups'][0]['section_um'][0] = -1
    out['groups'][0]['bundle_packings'][0]['section_um'][0] = -1
    assert view == before
    dims = [L, 30000, 20000]
    p = packing.pack_section(6, '10', '1', dims, False)
    assert dims == [L, 30000, 20000]
    p['section_um'][0] = 1
    assert dims == [L, 30000, 20000]


# ---------------------------------------------------------------- group / revision
def group(gid='G', pieces=6, od='10', dims=(L, 30000, 20000), n=3, warn=False, issues=(), overrides=None):
    return {'group_id': gid, 'pieces_per_bundle': pieces, 'outside_diameter_mm': od, 'wall_thickness_mm': '1',
            'dimensions_um': list(dims), 'dimension_warning': warn, 'issue_codes': list(issues),
            'bundle_ids': [f'{gid}-B{i:04d}' for i in range(1, n + 1)], 'bundle_overrides': overrides or {}}


def test_pack_group_shape_and_source_warning_rules():
    g = pack_g = packing.pack_group(group())
    assert g['group_id'] == 'G' and g['bundle_count'] == 3 and g['bundle_packings'] == [] and g['status'] == 'DETAILED'
    assert codes(packing.pack_group(group(warn=True))) == ['SOURCE_WARNING']
    assert codes(packing.pack_group(group(issues=['x']))) == ['SOURCE_WARNING']
    assert pack_g['pipe_centres_um'] == sec(6, '10', 30000, 20000)['pipe_centres_um']


def test_bundle_override_dimensions_gives_bundle_packing_in_bundle_id_order():
    ov = {'G-B0003': {'dimensions_um': [L, 15000, 15000]}, 'G-B0001': {'dimensions_um': [L, 60000, 60000], 'mass_g': 5},
          'G-B0002': {'mass_g': 7}, 'G-X': {'dimensions_um': [L, 1, 1]}}
    g = packing.pack_group(group(overrides=ov, warn=True))
    assert g['status'] == 'DETAILED' and g['bundle_count'] == 3
    assert [b['bundle_id'] for b in g['bundle_packings']] == ['G-B0001', 'G-B0003']
    b1, b3 = g['bundle_packings']
    assert b1['status'] == 'DETAILED' and b1['section_um'] == [60000, 60000] and b1['od_um'] == 10000
    assert 'ENVELOPE_LOOSE' in codes(b1) and 'SOURCE_WARNING' in codes(b1)
    assert b3['status'] == 'ENVELOPE_ONLY' and codes(b3) == ['PIECES_DO_NOT_FIT', 'SOURCE_WARNING'] and b3['max_fit'] == 1
    assert b3['pieces_source'] == 6 and b3['pieces_placed'] == 0


def test_pack_revision_stats_with_overrides():
    base = packing.pack_revision(VIEW)
    view = copy.deepcopy(VIEW)
    g = next(x for x in view['groups'] if x['group_id'] == 'Sheet1-R002')  # 42 pieces, 160 bundles
    g['bundle_overrides'][g['bundle_ids'][0]] = {'dimensions_um': [6401000, 100000, 100000]}  # cannot fit
    g['bundle_overrides'][g['bundle_ids'][1]] = {'dimensions_um': [6401000, 600000, 600000]}  # fits
    g['bundle_overrides'][g['bundle_ids'][2]] = {'mass_g': 9}  # no dims -> inherits
    out = packing.pack_revision(view)
    bs, b0 = out['stats'], base['stats']
    assert bs['groups_by_status'] == b0['groups_by_status'] and bs['bundle_count'] == b0['bundle_count']
    assert bs['bundles_by_status']['ENVELOPE_ONLY'] == b0['bundles_by_status']['ENVELOPE_ONLY'] + 1
    assert bs['bundles_by_status']['DETAILED'] == b0['bundles_by_status']['DETAILED'] - 1
    assert bs['derived_pieces'] == b0['derived_pieces'] - 42 and bs['source_pieces'] == b0['source_pieces']
    og = next(x for x in out['groups'] if x['group_id'] == 'Sheet1-R002')
    assert [b['bundle_id'] for b in og['bundle_packings']] == g['bundle_ids'][:2]
    assert [b['status'] for b in og['bundle_packings']] == ['ENVELOPE_ONLY', 'DETAILED']
    assert og['bundle_count'] == 160 and og['status'] == 'DETAILED'


def test_one_broken_group_does_not_affect_others():
    base = packing.pack_revision(VIEW)
    for key, bad in (('outside_diameter_mm', 'abc'), ('pieces_per_bundle', 0), ('dimensions_um', [1, 2]),
                     ('outside_diameter_mm', None)):
        view = copy.deepcopy(VIEW)
        view['groups'][5][key] = bad
        out = packing.pack_revision(view)
        assert out['groups'][5]['status'] == 'ENVELOPE_ONLY'
        for i, (a, b) in enumerate(zip(base['groups'], out['groups'])):
            if i != 5:
                assert a == b
        assert out['stats']['groups_by_status'] == {'DETAILED': 27, 'ENVELOPE_ONLY': 4}
    view = copy.deepcopy(VIEW)
    for k in ('outside_diameter_mm', 'dimensions_um', 'bundle_overrides'):
        del view['groups'][5][k]  # missing keys do not raise either
    out = packing.pack_revision(view)
    assert out['groups'][5]['status'] == 'ENVELOPE_ONLY'
    assert [g for i, g in enumerate(out['groups']) if i != 5] == [g for i, g in enumerate(base['groups']) if i != 5]


def test_empty_revision_stats_have_both_status_keys():
    out = packing.pack_revision({'revision_id': 'X@R0000', 'content_sha256': 'ab', 'groups': []})
    assert out['stats'] == {'group_count': 0, 'groups_by_status': {'DETAILED': 0, 'ENVELOPE_ONLY': 0}, 'bundle_count': 0,
                            'bundles_by_status': {'DETAILED': 0, 'ENVELOPE_ONLY': 0}, 'derived_pieces': 0, 'source_pieces': 0}
    assert out['groups'] == [] and out['basis'] == 'DERIVED'


# ---------------------------------------------------------------- R0000
def test_r0000_envelope_keys_and_types():
    out = packing.pack_revision(VIEW)
    assert set(out) == {'dataset_id', 'revision_id', 'content_sha256', 'basis', 'groups', 'stats'}
    assert out['dataset_id'] == cr.DATASET and out['revision_id'] == VIEW['revision_id']
    assert out['content_sha256'] == VIEW['content_sha256'] and out['basis'] == 'DERIVED'
    core = {'status', 'basis', 'layout', 'columns', 'rows', 'od_um', 'wall_thickness_um', 'length_um', 'section_um',
            'pieces_source', 'pieces_placed', 'max_fit', 'pipe_centres_um', 'slack_um', 'checks', 'reasons'}
    for g in out['groups']:
        assert set(g) == core | {'group_id', 'bundle_count', 'bundle_packings'}
        assert set(g['checks']) == {'count', 'od_fit', 'envelope_fit', 'slack_loose'}
        assert g['bundle_packings'] == []
    assert set(out['stats']) == {'group_count', 'groups_by_status', 'bundle_count', 'bundles_by_status', 'derived_pieces',
                                 'source_pieces'}


def test_r0000_expected_statuses():
    out = packing.pack_revision(VIEW)
    broken = {'Sheet1-R022', 'Sheet1-R031', 'Sheet1-R032'}
    assert len(out['groups']) == 31
    for g in out['groups']:
        if g['group_id'] in broken:
            assert g['status'] == 'ENVELOPE_ONLY' and g['section_um'] == [438200, 438200] and g['od_um'] == 219100
            assert codes(g) == ['PIECES_DO_NOT_FIT', 'SOURCE_WARNING'] and g['pieces_source'] == 5 and g['max_fit'] == 4
        else:
            assert g['status'] == 'DETAILED', g['group_id']
            assert g['layout'] in ('RECT', 'HEX')
            assert g['checks']['count'] and g['checks']['od_fit'] and g['checks']['envelope_fit']
            assert_inside(g)


def test_r0000_detailed_groups_conserve_pieces_and_stats_totals():
    out = packing.pack_revision(VIEW)
    by_id = {g['group_id']: g for g in VIEW['groups']}
    derived = source = 0
    n_bundles = {'DETAILED': 0, 'ENVELOPE_ONLY': 0}
    for g in out['groups']:
        src = by_id[g['group_id']]
        assert g['bundle_count'] == src['bundle_count'] == len(src['bundle_ids'])
        assert g['pieces_source'] == src['pieces_per_bundle']
        n_bundles[g['status']] += g['bundle_count']
        derived += g['pieces_placed'] * g['bundle_count']
        source += src['pieces_per_bundle'] * g['bundle_count']
        if g['status'] == 'DETAILED':
            assert g['pieces_placed'] * g['bundle_count'] == src['pieces_per_bundle'] * g['bundle_count']
            assert len(g['pipe_centres_um']) == g['pieces_placed']
        else:
            assert g['pieces_placed'] == 0
    s = out['stats']
    assert s['group_count'] == 31 and s['groups_by_status'] == {'DETAILED': 28, 'ENVELOPE_ONLY': 3}
    assert s['bundle_count'] == sum(g['bundle_count'] for g in VIEW['groups'])
    assert s['bundles_by_status'] == n_bundles and sum(n_bundles.values()) == s['bundle_count']
    assert s['derived_pieces'] == derived and s['source_pieces'] == source
    assert s['source_pieces'] - s['derived_pieces'] == 5 * (12 + 1 + 3)
