"""Verify release checksums without editing the package. Python 3.10+."""
from pathlib import Path
import hashlib
import sys

root = Path(__file__).resolve().parents[1]
manifest = root / 'FILE_CHECKSUMS.sha256'
if not manifest.is_file():
    print('FAIL: FILE_CHECKSUMS.sha256 is missing')
    raise SystemExit(1)
count = 0
failures = []
seen = set()
for line in manifest.read_text(encoding='utf-8').splitlines():
    if not line:
        continue
    try:
        expected, relative = line.split('  ', 1)
        path = (root / relative).resolve()
        if path == root or not path.is_relative_to(root) or relative in seen:
            raise ValueError('invalid or duplicate path')
        seen.add(relative)
        if len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
            raise ValueError('invalid checksum')
        if not path.is_file():
            raise ValueError('missing file')
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('checksum mismatch')
        count += 1
    except (ValueError, OSError) as exc:
        failures.append(f'{line}: {exc}')
if failures:
    print('FAIL: package contents differ from release manifest')
    for failure in failures:
        print(failure)
    raise SystemExit(1)
print(f'PASS: {count} listed release files match their SHA-256 checksums.')
print('Checksum integrity is not proof of author identity, runtime correctness, or operational eligibility.')
