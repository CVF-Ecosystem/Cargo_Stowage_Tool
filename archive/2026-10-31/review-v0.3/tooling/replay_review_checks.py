"""Replay the frozen v0.2 reference suite and R2 probes into a new external folder.

This is review tooling, not an application backend or operational validator.
Usage: python tooling/replay_review_checks.py --output ../scst-review-run-001
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = 'Steel_Cargo_Stowage_Tool_v0.2_Official_Local_Agent_Package.zip'
ARCHIVE_SHA256 = '6f587938f48b24daef5eaf0ba3fcab7532ec0397c3d2f7a39ca2caf686da44df'
INNER_NAME = 'Steel_Cargo_Stowage_Tool_v0.2_Local_Agent_Package'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error('Output must be outside the review package')
    if out.exists():
        parser.error('Choose a new output directory; existing evidence is never overwritten')
    archive = ROOT / 'history' / ARCHIVE_NAME
    if digest(archive) != ARCHIVE_SHA256:
        parser.error('Frozen v0.2 archive digest differs from the reviewed release')
    out.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    extract_dir = out / 'frozen_v02'
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            p = PurePosixPath(info.filename)
            if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] != INNER_NAME:
                raise ValueError('Unexpected archive path')
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError('Symlink entry is not accepted')
        if z.testzip() is not None:
            raise ValueError('Archive CRC check failed')
        z.extractall(extract_dir)
    frozen = extract_dir / INNER_NAME
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    steps = []
    commands = [
        ('v02_checksum', [sys.executable, str(frozen / 'tooling/verify_package.py')]),
        ('v02_reference_tests', [sys.executable, str(frozen / 'tests/run_all.py'), '--output', str(out / 'reference')]),
        ('r2_contract_probes', [sys.executable, str(ROOT / 'probes/replay_r2_contract_probes.py'), '--package-root', str(frozen), '--output', str(out / 'probes')]),
    ]
    for name, command in commands:
        result = subprocess.run(command, cwd=frozen, env=env, capture_output=True, text=True, encoding='utf-8')
        log = out / f'{name}.log'
        log.write_text(result.stdout + result.stderr, encoding='utf-8')
        steps.append({'step': name, 'command': command, 'cwd': str(frozen), 'exitCode': result.returncode, 'log': str(log), 'logSha256': digest(log)})
        print(f'{name}: exit {result.returncode}; log={log}')
        if result.returncode:
            break
    receipt = {
        'receiptKind': 'REVIEW_REFERENCE_REPLAY_ONLY', 'startedAt': started,
        'finishedAt': datetime.now(timezone.utc).isoformat(),
        'command': [sys.executable, *sys.argv], 'frozenV02Sha256': digest(archive),
        'replayScriptSha256': digest(Path(__file__)),
        'probeScriptSha256': digest(ROOT / 'probes/replay_r2_contract_probes.py'),
        'steps': steps, 'completed': len(steps) == 3 and all(x['exitCode'] == 0 for x in steps),
        'operationalEligible': False,
        'notEvaluated': ['Application backend and authenticated identity', 'Production solver and UI', 'CVF source/runtime integration', 'Real cargo, hold, support and field approval'],
    }
    (out / 'review_replay_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('REVIEW REPLAY ONLY; operationalEligible=false; no product gate is granted.')
    return 0 if receipt['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
