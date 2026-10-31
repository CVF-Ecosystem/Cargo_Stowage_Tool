"""Reproduce schema/domain scope observations. Does not mutate the v0.2 package."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

sys.dont_write_bytecode = True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.package_root.resolve()
    output = args.output.resolve()
    containing_package = Path(__file__).resolve().parents[1]
    if output == root or root in output.parents or output == containing_package or containing_package in output.parents:
        parser.error('Output must be outside both the released v0.2 package and this review package')
    sys.path.insert(0, str(root))
    from reference.validator import schema_errors, validate_bundle
    def fixture(name):
        return json.loads((root/'tests/fixtures'/f'{name}.json').read_text())
    probes = []
    def schema_probe(probe_id, kind, value, meaning):
        errors = schema_errors(kind, value)
        probes.append({'id': probe_id, 'scope': 'JSON_SCHEMA_ONLY',
                       'schemaAccepted': not errors, 'errors': errors,
                       'meaning': meaning, 'operationalPermissionTested': False})
    m = fixture('manifest')
    m['testOnly'] = False
    schema_probe('R2-02-MANIFEST', 'manifest', m,
                 'testOnly=false with VERIFIED, SYNTHETIC source and SYNTHETIC unit masses fits schema; no operational admission is being exercised')
    v = fixture('vessel_profile')
    v['testOnly'] = False
    schema_probe('R2-02-VESSEL', 'vessel_profile', v,
                 'testOnly=false with synthetic cargo-limit evidence fits schema; no source registry is being queried')
    m = fixture('manifest')
    m['testOnly'] = False
    m['source']['sourceType'] = 'DOCUMENT'
    for unit in m['cargoUnits']:
        unit['massBasis'] = 'DECLARED'
    m['cargoUnits'][0]['sourceLineId'] = 'nonexistent-row-with-no-resolver'
    m['cargoUnits'][0]['massKg'] += 1
    m['declaredTotalMassKg'] += 1
    schema_probe('R2-08-NO-FIELD-LINK', 'manifest', m,
                 'A sourceLineId is free text; changing a value and total cannot be checked against source/draft/confirmation by this schema. Relabeling a synthetic fixture is a deliberately invalid domain input, not a real document.')
    m = fixture('manifest')
    m['cargoUnits'][0]['massKg'] = 2000.5
    m['declaredTotalMassKg'] = 4000.5
    schema_probe('R2-04-FRACTIONAL-KG', 'manifest', m,
                 'Fractional kg is correctly rejected by v0.2 integer-kg schema; this says nothing about precision of actual user manifests')
    bundle = fixture('valid_bundle')
    report = validate_bundle(copy.deepcopy(bundle), fixture_mode=False)
    probes.append({'id': 'REFERENCE-NO-OPERATIONAL-PATH',
                   'scope': 'REFERENCE_CONTRACT_ONLY',
                   'contractChecksPass': report['contractChecksPass'],
                   'operationalEligible': report['operationalEligible'],
                   'issues': report['issues'],
                   'meaning': 'Production mode does not exist; default invocation keeps eligibility false'})
    expected = [True, True, True, False]
    observed = [p['schemaAccepted'] for p in probes[:4]]
    assert observed == expected, (observed, expected)
    assert report['operationalEligible'] is False
    inputs = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ['contracts/schemas', 'reference', 'tests/fixtures']
              for p in sorted((root/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    result = {'auditKind': 'R3_REPRODUCTION_OF_R2_CONTRACT_OBSERVATIONS',
              'timestamp': datetime.now(timezone.utc).isoformat(),
              'command': [sys.executable, *sys.argv],
              'runtime': {'python': platform.python_version(), 'jsonschema': importlib.metadata.version('jsonschema')},
              'expectedObservationsReproduced': True, 'probes': probes,
              'inputFileSha256': inputs,
              'limitations': ['No production backend exists in this package',
                              'Schema acceptance is not an authorization bypass',
                              'Source authenticity, real identity and persistence are not tested']}
    output.mkdir(parents=True, exist_ok=True)
    (output/'r2_contract_probe_receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'observationsReproduced': True, 'probeCount': len(probes),
                      'schemaAcceptance': observed, 'operationalEligible': False,
                      'receipt': str(output/'r2_contract_probe_receipt.json')}, indent=2))

if __name__ == '__main__':
    main()
