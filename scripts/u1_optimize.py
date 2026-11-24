"""Bounded, explicit process alternatives; no geometry, speed or color edits."""
from __future__ import annotations
import json
import math
from pathlib import Path
import shutil
import zipfile
try:
    from . import u1_3mf
except ImportError:
    import u1_3mf

PATTERNS = {'gyroid', 'cubic', 'adaptivecubic', 'grid', 'rectilinear'}
SUPPORT_TYPES = {'normal(auto)', 'tree(auto)'}
MUTABLE = {'sparse_infill_pattern', 'sparse_infill_density', 'support_type'}
GUARDED = MUTABLE | {'wall_loops', 'layer_height', 'top_shell_layers', 'top_shell_thickness',
                     'bottom_shell_layers', 'bottom_shell_thickness', 'enable_support'}


def _number(value, label):
    if isinstance(value, bool):
        raise ValueError(f'{label} must be numeric')
    try:
        result = float(str(value).rstrip('%'))
    except (ValueError, TypeError) as exc:
        raise ValueError(f'{label} must be numeric') from exc
    if not math.isfinite(result):
        raise ValueError(f'{label} must be finite')
    return result


def load_constraints(path):
    path = Path(path)
    if path.stat().st_size > 65536:
        raise ValueError('constraints exceed 64 KiB')
    policy = json.loads(path.read_text(encoding='utf-8'))
    allowed = {'minimum_walls', 'minimum_infill_percent', 'maximum_layer_height_mm',
               'minimum_top_thickness_mm', 'minimum_bottom_thickness_mm',
               'infill_patterns', 'infill_percentages', 'support_types', 'max_candidates'}
    if not isinstance(policy, dict) or set(policy) - allowed:
        raise ValueError('constraints must contain only documented constraint keys')
    for key, lower, upper in [('minimum_walls', 1, 20), ('minimum_infill_percent', 0, 100),
                               ('maximum_layer_height_mm', 0.01, 0.4)]:
        value = _number(policy.get(key), key)
        if not lower <= value <= upper or key == 'minimum_walls' and not value.is_integer():
            raise ValueError(f'{key} is outside its supported range')
        policy[key] = value
    for key in ('minimum_top_thickness_mm', 'minimum_bottom_thickness_mm'):
        if key in policy:
            value = _number(policy[key], key)
            if not 0 <= value <= 100:
                raise ValueError(f'{key} is outside its supported range')
            policy[key] = value
    count = policy.get('max_candidates', 4)
    if type(count) is not int or not 1 <= count <= 6:
        raise ValueError('max_candidates must be an integer from 1 to 6 (including baseline/layout runs)')
    policy['max_candidates'] = count
    for key, choices in [('infill_patterns', PATTERNS), ('support_types', SUPPORT_TYPES)]:
        values = policy.get(key, [])
        if not isinstance(values, list) or len(values) > 5 or any(not isinstance(v, str) or v not in choices for v in values):
            raise ValueError(f'{key} must list supported values')
        policy[key] = list(dict.fromkeys(values))
    values = policy.get('infill_percentages', [])
    if not isinstance(values, list) or len(values) > 5:
        raise ValueError('infill_percentages must be a list of at most five values')
    policy['infill_percentages'] = []
    for value in values:
        value = _number(value, 'infill_percentages')
        if not policy['minimum_infill_percent'] <= value <= 100:
            raise ValueError('candidate infill is below the declared minimum or above 100%')
        if value not in policy['infill_percentages']:
            policy['infill_percentages'].append(value)
    return policy


def read_settings(path):
    with zipfile.ZipFile(path) as archive:
        u1_3mf.validate_archive(archive)
        settings = json.loads(u1_3mf.read_member(archive, 'Metadata/project_settings.config'))
        u1_3mf.reject_post_process(settings)
        return settings


def constraint_check(path, policy, *, baseline=None):
    settings = read_settings(path)
    original = read_settings(baseline) if baseline else settings
    reasons = []
    with zipfile.ZipFile(path) as archive:
        config = u1_3mf.parse_xml(u1_3mf.read_member(archive, 'Metadata/model_settings.config', u1_3mf.MAX_MEMBER_BYTES))
        if any(entry.get('key') in GUARDED for obj in [*config.findall('object'), *config.findall('plate')] for entry in obj.iter('metadata')):
            reasons.append('per-object/per-plate process overrides require manual constraint evaluation')
        if any('layer_config_ranges' in name.lower() or 'layer_heights_profile' in name.lower() for name in archive.namelist()):
            reasons.append('adaptive/range layers require manual constraint evaluation')
    try:
        walls = _number(settings.get('wall_loops'), 'wall_loops')
        infill = _number(settings.get('sparse_infill_density'), 'sparse_infill_density')
        layer = _number(settings.get('layer_height'), 'layer_height')
        if walls < max(policy['minimum_walls'], _number(original.get('wall_loops'), 'original wall_loops')):
            reasons.append('wall count is below the requirement or original')
        if infill < policy['minimum_infill_percent']:
            reasons.append('infill is below the declared minimum')
        if layer <= 0 or layer > min(policy['maximum_layer_height_mm'], _number(original.get('layer_height'), 'original layer_height')):
            reasons.append('layer height exceeds the requirement or original')
        for face in ('top', 'bottom'):
            def thickness(data):
                return max(_number(data.get(f'{face}_shell_thickness'), f'{face}_shell_thickness'),
                           _number(data.get(f'{face}_shell_layers'), f'{face}_shell_layers') * _number(data.get('layer_height'), 'layer_height'))
            minimum = max(policy.get(f'minimum_{face}_thickness_mm', 0), thickness(original))
            if thickness(settings) + 1e-9 < minimum:
                reasons.append(f'{face} shell is thinner than the requirement or original')
    except ValueError as exc:
        reasons.append(str(exc))
    return {'passed': not reasons, 'reasons': reasons, 'requirements': policy,
            'scope': 'Declared global software limits only; no physical strength, finish, load or support-removability certification.'}


def variants(settings, policy):
    """One factor at a time; caller caps TOTAL slices using max_candidates."""
    candidates = [('infill', 'sparse_infill_pattern', policy['infill_patterns']),
                  ('density', 'sparse_infill_density', [f'{v:g}%' for v in policy['infill_percentages']]),
                  ('support', 'support_type', policy['support_types'] if settings.get('enable_support') == '1' else [])]
    for label, key, values in candidates:
        for index, value in enumerate(values):
            if settings.get(key) != value:
                yield f'{label}-{index+1}', {key: value}


def write_variant(source, output, changes):
    """Write a fresh native working copy, retaining recipes and model data."""
    source, output = Path(source).resolve(), Path(output).resolve()
    if output == source or output.exists() or not changes or set(changes) - MUTABLE:
        raise ValueError('variant needs a fresh output and only supported process changes')
    settings = read_settings(source)
    for key, value in changes.items():
        if (key == 'sparse_infill_pattern' and value not in PATTERNS or
                key == 'support_type' and value not in SUPPORT_TYPES):
            raise ValueError('unsupported process alternative')
        if key == 'sparse_infill_density' and not 0 <= _number(value, key) <= 100:
            raise ValueError('invalid candidate density')
        settings[key] = value
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive, zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as target:
        u1_3mf.validate_archive(archive)
        for item in archive.infolist():
            name = item.filename
            if name.lower().endswith(('.gcode', '.gcode.md5')) or name == 'Metadata/slice_info.config':
                continue
            if name == 'Metadata/project_settings.config':
                target.writestr(name, json.dumps(settings))
            else:
                # Stream unchanged assets rather than holding a second large model in memory.
                with archive.open(item) as incoming, target.open(name, 'w') as outgoing:
                    shutil.copyfileobj(incoming, outgoing, length=1024*1024)
    return output
