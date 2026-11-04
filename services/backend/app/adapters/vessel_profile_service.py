"""Vessel profiles for the API and plan binding (SUP-02B D3-D5): built-in VINAFCO268 v1 plus the append-only user store.

Pure orchestration over domain.vessel_profiles, adapters.vessel_profile_store and the read-only built-in data.
Nothing here repairs, edits or deletes a stored profile.
"""
import base64
import binascii
import hashlib
import json
from functools import lru_cache

from ..demo import demo_plan
from ..domain.model import Plan
from ..domain.rules import evaluate
from ..domain.vessel_profiles import (canonical_bytes, check_profile_size, profile_sha256, validate_profile, verify,
                                      viewer_block)
from ..domain.vessel_profiles.glb import MAX_GLB_BYTES, GlbError, glb_bounds, parse_glb
from ..vessel import DATA, builtin_vinafco_profile
from . import vessel_profile_store as store
from .plan_binding import PlanBindingError, bind
from .vessel_profile_store import ProfileUnavailable, StoreError, StoreLimit, VersionConflict

MAX_BODY_BYTES = 28 * 1024 * 1024
BUILTIN_ID = 'VINAFCO268'
BUILTIN_URL = '/api/vessels/vinafco268/model'


class ServiceError(Exception):
    """An HTTP-mappable failure: `detail` is the JSON body of the error response."""

    def __init__(self, status: int, detail):
        super().__init__(str(detail))
        self.status, self.detail = status, detail


def _err(field: str, message: str) -> dict:
    return {'field': field, 'message': message}


def body_size_errors(n_bytes: int) -> list[dict]:
    if n_bytes > MAX_BODY_BYTES:
        return [_err('body', f'Thân yêu cầu dài {n_bytes} byte, vượt giới hạn 28 MiB ({MAX_BODY_BYTES} byte).')]
    return []


# ------------------------------------------------------------------ records
@lru_cache(maxsize=1)
def _builtin() -> dict:
    model, errors = validate_profile(builtin_vinafco_profile())
    assert not errors
    glb = (DATA / 'model.glb').read_bytes()
    verification = verify(model, glb_bounds(parse_glb(glb)))
    return {'builtin': True, 'profile': model, 'profile_sha256': profile_sha256(model), 'glb_sha256': hashlib.sha256(glb).hexdigest(),
            'verification': verification, 'created_utc': None, 'asset_url': BUILTIN_URL, 'glb_bytes': glb}


def _load(profile_id: str, version: int) -> dict:
    """Record of one servable profile version. LookupError if unknown; ProfileUnavailable if it fails integrity."""
    if profile_id == BUILTIN_ID:
        if version != 1:
            raise LookupError(f'Không tìm thấy hồ sơ tàu {profile_id} phiên bản {version}.')
        return _builtin()
    stored = store.read(profile_id, version)
    manifest = stored['manifest']

    def bad(reason):
        return ProfileUnavailable(profile_id, version, reason)

    try:
        data = json.loads(stored['profile_bytes'].decode('utf-8'))
    except (UnicodeDecodeError, ValueError):
        raise bad('profile.json không phải JSON hợp lệ.') from None
    model, errors = validate_profile(data)
    if errors or model.id != profile_id or model.version != version or profile_sha256(model) != manifest['profile_sha256']:
        raise bad('profile.json không còn hợp lệ hoặc không khớp mã, phiên bản, sha256.')
    return {'builtin': False, 'profile': model, 'profile_sha256': manifest['profile_sha256'], 'glb_sha256': manifest['glb_sha256'],
            'verification': manifest['verification'], 'created_utc': manifest['created_utc'], 'glb_bytes': stored['glb_bytes'],
            'asset_url': f'/api/vessel-profiles/{profile_id}/{version}/model'}


def _item(rec: dict) -> dict:
    p = rec['profile']
    return {'id': p.id, 'version': p.version, 'name': p.name, 'registration': p.registration, 'builtin': rec['builtin'],
            'status': 'AVAILABLE', 'integrity_error': None, 'verification': rec['verification']['result'],
            'field_status': p.provenance.field_status.model_dump(mode='json'),
            'source_documents': [d.model_dump(mode='json') for d in p.provenance.source_documents],
            'profile_sha256': rec['profile_sha256'], 'created_utc': rec['created_utc']}


def _created_hint(profile_id: str, version: int):
    try:
        value = json.loads((store.data_dir() / profile_id / f'v{version}' / 'manifest.json').read_bytes()).get('created_utc')
        return value if isinstance(value, str) else None
    except (OSError, ValueError, AttributeError):
        return None


def list_profiles() -> list[dict]:
    """User versions (newest first, unservable ones flagged UNAVAILABLE) then the built-ins."""
    users = []
    for profile_id in store.list_ids():
        for version in store.versions(profile_id):
            try:
                item = _item(_load(profile_id, version))
            except (ProfileUnavailable, LookupError) as exc:
                item = {'id': profile_id, 'version': version, 'name': profile_id, 'registration': None, 'builtin': False,
                        'status': 'UNAVAILABLE', 'integrity_error': str(exc), 'verification': None, 'field_status': None,
                        'source_documents': [], 'profile_sha256': None, 'created_utc': _created_hint(profile_id, version)}
            users.append(item)
    users.sort(key=lambda i: (i['created_utc'] or '', i['id'], i['version']), reverse=True)
    return users + [_item(_builtin())]


def detail(profile_id: str, version: int) -> dict:
    rec = _load(profile_id, version)
    return {'id': profile_id, 'version': version, 'builtin': rec['builtin'], 'status': 'AVAILABLE',
            'profile': rec['profile'].model_dump(mode='json'), 'profile_sha256': rec['profile_sha256'],
            'glb_sha256': rec['glb_sha256'], 'asset_url': rec['asset_url'], 'verification': rec['verification'],
            'viewer': viewer_block(rec['profile']), 'created_utc': rec['created_utc']}


def model_bytes(profile_id: str, version: int) -> bytes:
    return _load(profile_id, version)['glb_bytes']


# ------------------------------------------------------------------ preview and create
def _evaluate_body(raw: bytes):
    """-> (preview payload, profile model | None, glb bytes | None). Never writes."""
    errors = body_size_errors(len(raw))
    profile = glb = verification = None
    glb_sha = None
    if not errors:
        try:
            body = json.loads(raw)
        except (ValueError, RecursionError):
            body = None
            errors.append(_err('body', 'Thân yêu cầu không phải JSON hợp lệ.'))
        if body is not None:
            if not isinstance(body, dict):
                errors.append(_err('body', 'Thân yêu cầu phải là một đối tượng JSON có "profile" và "glb_base64".'))
            else:
                errors += [_err(k, 'Thiếu trường bắt buộc.') for k in ('profile', 'glb_base64') if k not in body]
                errors += [_err(k, 'Trường không được phép có trong thân yêu cầu.') for k in body if k not in ('profile', 'glb_base64')]
                if 'profile' in body:
                    profile = _check_profile(body['profile'], errors)
                if 'glb_base64' in body:
                    glb, bounds = _check_glb(body['glb_base64'], errors)
                    glb_sha = hashlib.sha256(glb).hexdigest() if glb is not None else None
                    if profile is not None and bounds is not None:
                        verification = verify(profile, bounds)
    pid = profile.id if profile else None
    latest = store.latest_version(pid) if pid else None
    builtin_conflict = pid == BUILTIN_ID
    version_ok = bool(profile) and profile.version == latest + 1
    valid = not errors and bool(verification) and verification['result'] == 'PASS' and not builtin_conflict and version_ok
    payload = {'valid': valid, 'errors': errors, 'verification': verification,
               'profile_sha256': profile_sha256(profile) if profile else None, 'glb_sha256': glb_sha,
               'glb_bytes': len(glb) if glb is not None else None, 'id': pid, 'version': profile.version if profile else None,
               'latest_version': latest, 'version_ok': version_ok, 'builtin_conflict': builtin_conflict}
    return payload, profile, glb


def _check_profile(data, errors):
    if not isinstance(data, dict):
        errors.append(_err('profile', 'Hồ sơ tàu phải là một đối tượng JSON.'))
        return None
    try:
        size = len(json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode())
    except (UnicodeEncodeError, RecursionError):
        errors.append(_err('profile', 'Hồ sơ chứa ký tự hoặc cấu trúc không hợp lệ.'))
        return None
    if size_errors := check_profile_size(size):
        errors += size_errors
        return None
    model, found = validate_profile(data)
    errors += [_err(e['field'] if e['field'] == 'profile' else 'profile.' + e['field'], e['message']) for e in found]
    if model is not None:
        try:
            canonical_bytes(model)
        except UnicodeEncodeError:
            errors.append(_err('profile', 'Hồ sơ chứa ký tự không hợp lệ.'))
            return None
    return model


def _check_glb(value, errors):
    if not isinstance(value, str):
        errors.append(_err('glb_base64', 'Giá trị phải là chuỗi base64.'))
        return None, None
    if len(value) // 4 * 3 > MAX_GLB_BYTES + 3:
        errors.append(_err('glb', 'Tệp GLB vượt quá giới hạn 20 MiB.'))
        return None, None
    try:
        glb = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        errors.append(_err('glb_base64', 'Chuỗi base64 không hợp lệ.'))
        return None, None
    try:
        return glb, glb_bounds(parse_glb(glb))
    except GlbError as exc:
        errors.append(_err('glb', str(exc)))
        return glb, None
    except (ValueError, TypeError, AttributeError, KeyError, RecursionError):
        errors.append(_err('glb', 'Cấu trúc glTF trong GLB không hợp lệ.'))
        return glb, None


def preview(raw: bytes) -> dict:
    return _evaluate_body(raw)[0]


def create(raw: bytes) -> dict:
    payload, profile, glb = _evaluate_body(raw)
    if payload['errors'] or payload['verification'] is None or payload['verification']['result'] != 'PASS':
        raise ServiceError(400, payload)
    if payload['builtin_conflict']:
        raise ServiceError(409, {'message': f'Mã {BUILTIN_ID} thuộc hồ sơ tàu có sẵn, không được tạo thêm phiên bản.', 'latest_version': None})
    try:
        store.append(profile.id, profile.version, canonical_bytes(profile), glb, payload['verification'])
    except VersionConflict as exc:
        raise ServiceError(409, {'message': str(exc), 'latest_version': exc.latest})
    except StoreLimit as exc:
        raise ServiceError(409, {'message': str(exc), 'latest_version': None})
    except StoreError as exc:
        raise ServiceError(400, {'message': str(exc), 'latest_version': None})
    return _item(_load(profile.id, profile.version))


# ------------------------------------------------------------------ plan references
def check_reference(plan: Plan) -> None:
    """Bind a plan's user-profile reference to the stored profile (D4.3); no-op for VINAFCO268 plans."""
    ref = plan.vessel
    if ref is None or ref.profile_version is None:
        return
    try:
        rec = _load(ref.vessel_id, ref.profile_version)
    except LookupError:
        raise PlanBindingError(f'Profile tàu {ref.vessel_id} phiên bản {ref.profile_version} không tồn tại.') from None
    except (ProfileUnavailable, OSError) as exc:
        raise PlanBindingError(str(exc)) from None
    name = f'{ref.vessel_id} phiên bản {ref.profile_version}'
    if rec['builtin'] or ref.profile_sha256 != rec['profile_sha256']:
        raise PlanBindingError(f'Mã băm sha256 của profile tàu {name} không khớp với phương án.')
    h = rec['profile'].hold
    if (plan.hold.id, plan.hold.name, plan.hold.length_mm, plan.hold.width_mm, plan.hold.height_mm, plan.hold.shape) != \
            (h.id, h.name, h.length_mm, h.width_mm, h.height_mm, 'BOX'):
        raise PlanBindingError(f'Hầm của phương án không khớp hầm trong profile tàu {name}.')
    case = next((c for c in rec['profile'].cases if c.id == ref.case_id), None)
    if case is None:
        raise PlanBindingError(f'Trường hợp tải {ref.case_id} không thuộc profile tàu {name}.')
    if plan.limits.certificate_cargo_limit_g != case.cargo_mass_g:
        raise PlanBindingError(f'Giới hạn tải theo giấy chứng nhận không bằng khối lượng hàng của trường hợp {ref.case_id} trong profile tàu {name}.')


def case_plan(profile_id: str, version: int, case_id: str):
    """Evaluation of the demo cargo in the profile's hold with the case limits (shared by the VINAFCO and profile routes)."""
    rec = _load(profile_id, version)
    case = next((c for c in rec['profile'].cases if c.id == case_id), None)
    if case is None:
        raise LookupError(f'Không tìm thấy trường hợp tải {case_id} trong hồ sơ tàu {profile_id}.')
    hold = rec['profile'].hold
    vessel = {'vessel_id': profile_id, 'case_id': case_id}
    if not rec['builtin']:
        vessel.update(profile_version=version, profile_sha256=rec['profile_sha256'])
    payload = demo_plan().model_dump()
    payload.update(source='MIXED_REFERENCE', vessel=vessel,
                   hold={k: getattr(hold, k) for k in ('id', 'name', 'length_mm', 'width_mm', 'height_mm')})
    payload['limits']['certificate_cargo_limit_g'] = payload['limits']['voyage_cargo_limit_g'] = case.cargo_mass_g
    return evaluate(bind(Plan.model_validate(payload)))
