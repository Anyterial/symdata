#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List

HUGO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = HUGO_ROOT / "static" / "data"
SYMMETRY_BASICS_PATH = DATA_ROOT / "symmetry_basics.json"
TRANSFORMATIONS_HM_ENTRY_PATH = DATA_ROOT / "transformations_hm_entry.json"
CONTENT_ROOT = HUGO_ROOT / "content"
HALL_ROOT = CONTENT_ROOT / "hall"
POINTGROUP_ROOT = CONTENT_ROOT / "pointgroup"

INDEX_FIELDS = [
    "hall_key",
    "hall_entry",
    "hall",
    "hall_latex",
    "hall_html",
    "hall_unicode",
    "hall_aliases",
    "hall_aliases_latex",
    "hall_aliases_html",
    "hall_aliases_unicode",
    "hm_entry",
    "hm_entry_latex",
    "hm_entry_html",
    "hm_entry_unicode",
    "hm_entry_aliases",
    "hm_entry_aliases_latex",
    "hm_entry_aliases_html",
    "hm_entry_aliases_unicode",
    "ita_number",
    "hm_short",
    "hm_short_aliases",
    "hm_short_aliases_latex",
    "hm_short_aliases_html",
    "hm_short_aliases_unicode",
    "hm_short_latex",
    "hm_short_html",
    "hm_short_unicode",
    "hm_full",
    "hm_full_latex",
    "hm_full_html",
    "hm_full_unicode",
    "hm_extended",
    "hm_extended_latex",
    "hm_extended_html",
    "hm_extended_unicode",
    "hm_universal",
    "hm_universal_aliases",
    "hm_universal_aliases_latex",
    "hm_universal_aliases_html",
    "hm_universal_aliases_unicode",
    "hm_universal_latex",
    "hm_universal_html",
    "hm_universal_unicode",
    "n_c",
    "it_coordinate_system_code",
    "n_c_aliases",
    "setting",
    "setting_plaintext",
    "crystal_system",
    "bravais_type",
    "centring_type",
    "point_group",
    "laue_class",
    "qualifier",
    "schoenflies",
    "schoenflies_latex",
    "schoenflies_html",
    "schoenflies_unicode",
    "is_reference_setting",
]


_TRANSFORMATIONS_PAYLOAD: Dict[str, Any] | None = None


def _log(message: str) -> None:
    print(f"[generate_hall_pages] {message}", flush=True)


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        return value
    return None


def _resolve_input_path(path: Path) -> Path:
    gz_path = path.with_name(f"{path.name}.gz")
    if gz_path.exists():
        return gz_path
    return path


def _load_json(path: Path) -> Any:
    source = _resolve_input_path(path)
    if not source.exists():
        raise FileNotFoundError(f"Missing {source}")
    if source.suffix == ".gz":
        with gzip.open(source, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    with source.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json_gz(path: Path, payload: Any) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")


def _normalize_schoenflies_html(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value
    # Keep italic letters in sub/sup, but force numeric-only parts upright.
    text = re.sub(r"<sub>\s*<i>\s*(\d+)\s*</i>\s*</sub>", r"<sub>\1</sub>", text)
    text = re.sub(r"<sup>\s*<i>\s*(\d+)\s*</i>\s*</sup>", r"<sup>\1</sup>", text)
    return text


def _markup(entry: Dict[str, Any], field: str, kind: str) -> Any:
    direct = entry.get(f"{field}_{kind}")
    if direct is not None:
        return direct
    markup = entry.get(f"{field}_markup")
    if isinstance(markup, dict):
        return markup.get(kind)
    return None


def _aliases_markup(entry: Dict[str, Any], field: str, kind: str) -> Any:
    direct = entry.get(f"{field}_aliases_{kind}")
    if direct is not None:
        return direct
    markup = entry.get(f"{field}_aliases_markup")
    if isinstance(markup, list):
        values = []
        for item in markup:
            if isinstance(item, dict) and item.get(kind) is not None:
                values.append(item[kind])
        return values or None
    return None


def _unwrap_data_list(payload: Any, key: str) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if isinstance(data, dict) and isinstance(data.get(key), list):
        return [item for item in data[key] if isinstance(item, dict)]
    if isinstance(payload.get(key), list):
        return [item for item in payload[key] if isinstance(item, dict)]
    return []


def _matrix_vector_from_affine(raw: Dict[str, Any]) -> tuple[Any, Any]:
    matrix = _first_non_empty(raw.get("transformation_matrix"), raw.get("P"), raw.get("matrix"))
    vector = _first_non_empty(raw.get("origin_shift"), raw.get("p"), raw.get("vector"))
    affine = raw.get("affine_transformation")
    if isinstance(affine, dict):
        matrix = _first_non_empty(affine.get("matrix"), matrix)
        vector = _first_non_empty(affine.get("vector"), raw.get("p"), raw.get("vector"), raw.get("origin_shift"))
    return matrix, vector


def _normalize_affine_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    record = dict(raw)
    matrix, vector = _matrix_vector_from_affine(record)
    affine = record.get("affine_transformation") if isinstance(record.get("affine_transformation"), dict) else {}
    record["transformation_matrix"] = matrix
    record["origin_shift"] = _first_non_empty(record.get("origin_shift"), vector)
    record["P"] = matrix
    record["p"] = vector
    record["xyz"] = _first_non_empty(record.get("xyz"), affine.get("xyz"))
    record["P_det"] = _first_non_empty(record.get("P_det"), record.get("det"), affine.get("det"))
    record["P_is_orthogonal"] = _first_non_empty(record.get("P_is_orthogonal"), record.get("is_orthogonal"), affine.get("is_orthogonal"))
    return record


def _normalize_op(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    op = _normalize_affine_record(raw)
    return op


def _centering_translations_xyz(entry: Dict[str, Any]) -> List[str] | None:
    """Render structured ``centering_translations`` vectors as ``x,y,z`` strings.

    The datasets store centering translations only as lists of exact fraction
    strings; the former parallel ``centering_translations_xyz`` field was
    removed from the generated data, so the display strings are derived here.
    """
    raw = entry.get("centering_translations") if isinstance(entry, dict) else None
    if not isinstance(raw, list):
        return None
    rendered: List[str] = []
    for vec in raw:
        if isinstance(vec, list) and vec:
            rendered.append(",".join(str(component) for component in vec))
    return rendered or None


def _normalize_ops_with_xyz(raw_ops: Any, raw_xyz: Any = None) -> List[Dict[str, Any]]:
    ops = raw_ops if isinstance(raw_ops, list) else []
    xyz_list = raw_xyz if isinstance(raw_xyz, list) else []
    normalized_ops: List[Dict[str, Any]] = []
    for idx, op in enumerate(ops):
        if not isinstance(op, dict):
            continue
        op_normalized = _normalize_op(op)
        if op_normalized.get("xyz") is None and idx < len(xyz_list):
            op_normalized["xyz"] = xyz_list[idx]
        normalized_ops.append(op_normalized)
    return normalized_ops


def _normalize_normalizer_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    normalized = dict(payload)
    normalized["symops"] = _normalize_ops_with_xyz(payload.get("symops"), payload.get("symops_xyz"))
    normalized["symops_mod_centering"] = _normalize_ops_with_xyz(
        payload.get("symops_mod_centering"),
        payload.get("symops_mod_centering_xyz"),
    )
    normalized["n_ops"] = _first_non_empty(payload.get("n_ops"), payload.get("n_symops"))
    normalized["n_coset_representatives"] = _first_non_empty(payload.get("n_coset_representatives"), payload.get("n_symops"))
    return normalized


def _load_transformations_payload() -> Dict[str, Any]:
    global _TRANSFORMATIONS_PAYLOAD
    if _TRANSFORMATIONS_PAYLOAD is not None:
        return _TRANSFORMATIONS_PAYLOAD

    source = _resolve_input_path(TRANSFORMATIONS_HM_ENTRY_PATH)
    if not source.exists():
        _TRANSFORMATIONS_PAYLOAD = {}
        return _TRANSFORMATIONS_PAYLOAD

    _log(f"Loading transformations datasets from {source}")
    payload = _load_json(source.with_suffix("") if source.suffix == ".gz" else source)
    _TRANSFORMATIONS_PAYLOAD = payload if isinstance(payload, dict) else {}
    return _TRANSFORMATIONS_PAYLOAD


def _pick_dataset(payload: Any, *keys: str) -> Any:
    if not isinstance(payload, dict):
        return {}

    for key in keys:
        value = payload.get(key)
        if isinstance(value, (dict, list)):
            return value

    data = payload.get("data")
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, (dict, list)):
                return value

    datasets = payload.get("datasets")
    if isinstance(datasets, dict):
        for key in keys:
            value = datasets.get(key)
            if isinstance(value, dict):
                return value

    entries = payload.get("entries")
    if isinstance(entries, dict):
        for key in keys:
            value = entries.get(key)
            if isinstance(value, dict):
                return value
        datasets = entries.get("datasets")
        if isinstance(datasets, dict):
            for key in keys:
                value = datasets.get(key)
                if isinstance(value, dict):
                    return value
    return {}


def _payload_context(payload: Any) -> Dict[str, Any]:
    """Return the context for collection keys directly below ``data``.

    Current JSON-LD headers place those terms in the property-scoped
    ``@context.data.@context`` type map. The root-context fallback keeps the
    generator able to read older copied datasets.
    """
    if not isinstance(payload, dict):
        return {}
    context = payload.get("@context")
    mappings: Dict[str, Any] = {}
    if isinstance(context, dict):
        mappings.update(context)
    elif isinstance(context, list):
        for item in context:
            if isinstance(item, dict):
                mappings.update(item)
    data_term = mappings.get("data")
    if isinstance(data_term, dict):
        scoped_context = data_term.get("@context")
        if isinstance(scoped_context, dict):
            return scoped_context
    return mappings


def _extract_field_doc_urls(payload: Any, dataset_keys: List[str] | None = None) -> Dict[str, str]:
    """Collect field -> OPTIMADE property-definition URLs from a JSON-LD @context.

    When ``dataset_keys`` is given, only the nested per-dataset contexts for
    those keys are used. Datasets in one file can map the same field name to
    different property definitions (e.g. ``symops`` for spacegroups vs
    pointgroups), so callers building page-type-specific maps must select the
    matching dataset context instead of flattening everything.
    """
    mappings = _payload_context(payload)

    urls: Dict[str, str] = {}

    def collect(mapping: Dict[str, Any]) -> None:
        for key, value in mapping.items():
            if isinstance(value, str) and value.startswith("http"):
                urls[key] = value
            elif isinstance(value, dict):
                item_id = value.get("@id")
                if isinstance(item_id, str) and item_id.startswith("http"):
                    urls[key] = item_id
                nested = value.get("@context")
                if isinstance(nested, dict):
                    collect(nested)

    if dataset_keys is None:
        collect(mappings)
        return urls

    for dataset_key in dataset_keys:
        value = mappings.get(dataset_key)
        if isinstance(value, dict):
            nested = value.get("@context")
            if isinstance(nested, dict):
                collect(nested)
    return urls


def _looks_like_pointgroup_map(raw_data: Any) -> bool:
    if not isinstance(raw_data, dict) or not raw_data:
        return False
    sample = next((value for value in raw_data.values() if isinstance(value, dict)), None)
    if sample is None:
        return False
    return any(
        key in sample
        for key in (
            "hm_symbol",
            "schoenflies",
            "symops",
            "conjugacy_classes",
            "character_table_real",
            "character_table_complex",
        )
    )


def _normalize_entry(hall_key: str, raw_entry: Any) -> Dict[str, Any]:
    entry = dict(raw_entry) if isinstance(raw_entry, dict) else {}

    hall_key_normalized = _first_non_empty(entry.get("hall_entry"), hall_key)
    hall_symbol = _first_non_empty(entry.get("hall"), entry.get("hall_symbol"), hall_key_normalized)
    hall_latex = _first_non_empty(_markup(entry, "hall", "latex"))
    hall_html = _first_non_empty(_markup(entry, "hall", "html"), _markup(entry, "hall", "unicode"), hall_symbol, hall_key_normalized)
    hall_unicode = _first_non_empty(_markup(entry, "hall", "unicode"), hall_symbol, hall_key_normalized)

    hm_universal_source = _first_non_empty(entry.get("hm_universal"), entry.get("hm_cctbx_universal"))
    hm_short = _first_non_empty(entry.get("hm_short"), entry.get("hm_full"), entry.get("hm_extended"), hm_universal_source)
    hm_short_aliases = _first_non_empty(entry.get("hm_short_aliases"))
    hm_short_aliases_latex = _first_non_empty(_aliases_markup(entry, "hm_short", "latex"), entry.get("hm_short_aliases_latex"), entry.get("hm_short_nonstd_aliases_latex"))
    hm_short_aliases_html = _first_non_empty(_aliases_markup(entry, "hm_short", "html"), entry.get("hm_short_aliases_html"), entry.get("hm_short_nonstd_aliases_html"))
    hm_short_aliases_unicode = _first_non_empty(_aliases_markup(entry, "hm_short", "unicode"), entry.get("hm_short_aliases_unicode"), hm_short_aliases)
    hm_short_latex = _first_non_empty(_markup(entry, "hm_short", "latex"), entry.get("hm_short_latex"), entry.get("hm_short_nonstd_latex"), _markup(entry, "hm_short_std", "latex"))
    hm_short_html = _first_non_empty(_markup(entry, "hm_short", "html"), entry.get("hm_short_html"), entry.get("hm_short_nonstd_html"), _markup(entry, "hm_short_std", "html"), hm_short)
    hm_short_unicode = _first_non_empty(_markup(entry, "hm_short", "unicode"), entry.get("hm_short_unicode"), hm_short)

    hm_full = _first_non_empty(entry.get("hm_full"), hm_short)
    hm_full_latex = _first_non_empty(_markup(entry, "hm_full", "latex"), entry.get("hm_full_latex"), entry.get("hm_full_nonstd_latex"), _markup(entry, "hm_full_std", "latex"))
    hm_full_html = _first_non_empty(_markup(entry, "hm_full", "html"), entry.get("hm_full_html"), entry.get("hm_full_nonstd_html"), _markup(entry, "hm_full_std", "html"), hm_full)
    hm_full_unicode = _first_non_empty(_markup(entry, "hm_full", "unicode"), entry.get("hm_full_unicode"), hm_short_unicode, hm_full)

    hm_extended = _first_non_empty(entry.get("hm_extended"), hm_full)
    hm_extended_latex = _first_non_empty(_markup(entry, "hm_extended", "latex"), entry.get("hm_extended_latex"))
    hm_extended_html = _first_non_empty(_markup(entry, "hm_extended", "html"), entry.get("hm_extended_html"), hm_full_html, hm_extended)
    hm_extended_unicode = _first_non_empty(_markup(entry, "hm_extended", "unicode"), entry.get("hm_extended_unicode"), hm_full_unicode, hm_extended)

    hm_universal = _first_non_empty(hm_universal_source, hm_extended)
    hm_universal_aliases = _first_non_empty(entry.get("hm_universal_aliases"), entry.get("hm_extended_aliases"))
    hm_universal_aliases_latex = _first_non_empty(entry.get("hm_universal_aliases_latex"), _aliases_markup(entry, "hm_extended", "latex"), entry.get("hm_extended_aliases_latex"))
    hm_universal_aliases_html = _first_non_empty(entry.get("hm_universal_aliases_html"), _aliases_markup(entry, "hm_extended", "html"), entry.get("hm_extended_aliases_html"))
    hm_universal_aliases_unicode = _first_non_empty(entry.get("hm_universal_aliases_unicode"), _aliases_markup(entry, "hm_extended", "unicode"), hm_universal_aliases)
    hm_universal_latex = _first_non_empty(entry.get("hm_universal_latex"))
    hm_universal_html = _first_non_empty(entry.get("hm_universal_html"), hm_extended_html, hm_universal)
    hm_universal_unicode = _first_non_empty(entry.get("hm_universal_unicode"), hm_extended_unicode, hm_universal)

    hm_entry = _first_non_empty(entry.get("hm_entry"), hm_full)
    hm_entry_latex = _first_non_empty(_markup(entry, "hm_entry", "latex"), hm_full_latex)
    hm_entry_html = _first_non_empty(_markup(entry, "hm_entry", "html"), hm_full_html, hm_entry)
    hm_entry_unicode = _first_non_empty(_markup(entry, "hm_entry", "unicode"), hm_full_unicode, hm_entry)
    hm_entry_aliases = _first_non_empty(entry.get("hm_entry_aliases"))
    hm_entry_aliases_latex = _first_non_empty(_aliases_markup(entry, "hm_entry", "latex"))
    hm_entry_aliases_html = _first_non_empty(_aliases_markup(entry, "hm_entry", "html"))
    hm_entry_aliases_unicode = _first_non_empty(_aliases_markup(entry, "hm_entry", "unicode"), hm_entry_aliases)

    n_c_aliases = _first_non_empty(entry.get("n_c_aliases"), entry.get("setting_it_nc_aliases"))

    normalized = dict(entry)
    normalized["hall_key"] = hall_key
    normalized["ita_number"] = _first_non_empty(entry.get("ita_number"), entry.get("it_number"))
    normalized["it_number"] = _first_non_empty(entry.get("it_number"), entry.get("ita_number"))
    normalized["hall"] = hall_symbol
    # Match the dataset convention: hall_entry is the normalized lookup key
    # (e.g. "p_1") and hall (+ markups) carries the display symbol ("P 1").
    normalized["hall_entry"] = hall_key_normalized
    normalized["hall_latex"] = hall_latex
    normalized["hall_html"] = hall_html
    normalized["hall_unicode"] = hall_unicode
    normalized["hall_aliases"] = _first_non_empty(entry.get("hall_aliases"))
    normalized["hall_aliases_latex"] = _first_non_empty(_aliases_markup(entry, "hall", "latex"), entry.get("hall_aliases_latex"))
    normalized["hall_aliases_html"] = _first_non_empty(_aliases_markup(entry, "hall", "html"), entry.get("hall_aliases_html"), entry.get("hall_alias_html"))
    normalized["hall_aliases_unicode"] = _first_non_empty(_aliases_markup(entry, "hall", "unicode"), entry.get("hall_aliases_unicode"), normalized["hall_aliases"])
    normalized["hm_entry"] = hm_entry
    normalized["hm_entry_latex"] = hm_entry_latex
    normalized["hm_entry_html"] = hm_entry_html
    normalized["hm_entry_unicode"] = hm_entry_unicode
    normalized["hm_entry_aliases"] = hm_entry_aliases
    normalized["hm_entry_aliases_latex"] = hm_entry_aliases_latex
    normalized["hm_entry_aliases_html"] = hm_entry_aliases_html
    normalized["hm_entry_aliases_unicode"] = hm_entry_aliases_unicode
    normalized["hm_short"] = hm_short
    normalized["hm_short_aliases"] = hm_short_aliases
    normalized["hm_short_aliases_latex"] = hm_short_aliases_latex
    normalized["hm_short_aliases_html"] = hm_short_aliases_html
    normalized["hm_short_aliases_unicode"] = hm_short_aliases_unicode
    normalized["hm_short_latex"] = hm_short_latex
    normalized["hm_short_html"] = hm_short_html
    normalized["hm_short_unicode"] = hm_short_unicode
    normalized["hm_full"] = hm_full
    normalized["hm_full_latex"] = hm_full_latex
    normalized["hm_full_html"] = hm_full_html
    normalized["hm_full_unicode"] = hm_full_unicode
    normalized["hm_extended"] = hm_extended
    normalized["hm_extended_latex"] = hm_extended_latex
    normalized["hm_extended_html"] = hm_extended_html
    normalized["hm_extended_unicode"] = hm_extended_unicode
    normalized["hm_universal"] = hm_universal
    normalized["hm_universal_aliases"] = hm_universal_aliases
    normalized["hm_universal_aliases_latex"] = hm_universal_aliases_latex
    normalized["hm_universal_aliases_html"] = hm_universal_aliases_html
    normalized["hm_universal_aliases_unicode"] = hm_universal_aliases_unicode
    normalized["hm_universal_latex"] = hm_universal_latex
    normalized["hm_universal_html"] = hm_universal_html
    normalized["hm_universal_unicode"] = hm_universal_unicode
    normalized["n_c_aliases"] = n_c_aliases
    normalized["n_c"] = _first_non_empty(entry.get("n_c"), entry.get("setting_it_nc"))
    normalized["setting_it_nc"] = normalized["n_c"]
    normalized["it_coordinate_system_code"] = _first_non_empty(entry.get("it_coordinate_system_code"))
    normalized["setting"] = _first_non_empty(entry.get("setting"))
    normalized["setting_plaintext"] = _first_non_empty(entry.get("setting_plaintext"), entry.get("settings_plaintext"))
    normalized["settings_plaintext"] = normalized["setting_plaintext"]
    normalized["qualifier"] = _first_non_empty(entry.get("qualifier"), normalized["setting"])

    normalized["centering_translations_xyz"] = _first_non_empty(
        entry.get("centering_translations_xyz"),
        _centering_translations_xyz(entry),
    )
    normalized["centering_translation_vector_count"] = _first_non_empty(
        entry.get("centering_translation_vector_count"),
        entry.get("n_centering_translations"),
        entry.get("n_ltr"),
    )
    normalized["pointgroup_symop_count"] = _first_non_empty(
        entry.get("pointgroup_symop_count"),
        entry.get("n_pointgroup_symops"),
        entry.get("n_smx"),
    )
    normalized["symop_count"] = _first_non_empty(
        entry.get("symop_count"),
        entry.get("n_symops"),
        entry.get("order_z"),
    )
    # Legacy aliases retained for template/backward compatibility.
    normalized["n_ltr"] = _first_non_empty(entry.get("n_ltr"), normalized["centering_translation_vector_count"])
    normalized["n_smx"] = _first_non_empty(entry.get("n_smx"), normalized["pointgroup_symop_count"])
    normalized["order_z"] = _first_non_empty(entry.get("order_z"), normalized["symop_count"])

    normalized["asu_ascii"] = _first_non_empty(entry.get("asu_ascii"), entry.get("asu_str"), entry.get("asym_unit"))
    normalized["asym_unit"] = _first_non_empty(entry.get("asym_unit"), normalized["asu_ascii"])

    normalized["schoenflies"] = _first_non_empty(entry.get("schoenflies"))
    normalized["schoenflies_latex"] = _first_non_empty(_markup(entry, "schoenflies", "latex"), entry.get("schoenflies_latex"))
    normalized["schoenflies_html"] = _normalize_schoenflies_html(
        _first_non_empty(_markup(entry, "schoenflies", "html"), entry.get("schoenflies_html"), normalized["schoenflies"])
    )
    normalized["schoenflies_unicode"] = _first_non_empty(_markup(entry, "schoenflies", "unicode"), entry.get("schoenflies_unicode"), normalized["schoenflies"])
    normalized["symops"] = _normalize_spacegroup_symops(entry, "symops")
    normalized["symops_mod_centering"] = _normalize_spacegroup_symops(entry, "symops_mod_centering")

    return normalized


def _normalize_spacegroup_symops(entry: Dict[str, Any], field: str = "symops") -> List[Dict[str, Any]]:
    raw_symops = entry.get(field)
    # The parallel ``*_xyz`` lists were removed from the dataset; xyz now lives
    # inside each operation's affine_transformation and is hoisted by
    # ``_normalize_op``. The xyz_list fallback is kept only for stale inputs.
    raw_xyz = entry.get(f"{field}_xyz")

    symops = raw_symops if isinstance(raw_symops, list) else []
    xyz_list = raw_xyz if isinstance(raw_xyz, list) else []

    if not symops:
        return []

    normalized_ops: List[Dict[str, Any]] = []
    for idx, op in enumerate(symops):
        if not isinstance(op, dict):
            continue
        op_normalized = _normalize_op(op)
        xyz = op_normalized.get("xyz")
        if xyz is None and idx < len(xyz_list):
            xyz = xyz_list[idx]
        op_normalized["xyz"] = xyz
        normalized_ops.append(op_normalized)

    return normalized_ops


def attach_hall_aliases(data: Dict[str, Dict[str, Any]]) -> None:
    def _as_alias_keys(raw_value: Any) -> List[str]:
        if isinstance(raw_value, list):
            values = raw_value
        elif raw_value is None:
            values = []
        else:
            values = [raw_value]
        keys: List[str] = []
        for value in values:
            text = str(value).strip()
            if text:
                keys.append(text)
        return keys

    by_key_or_entry: Dict[str, Dict[str, Any]] = {}
    for hall_key, entry in data.items():
        by_key_or_entry[hall_key] = entry
        hall_entry = str(entry.get("hall_entry") or "").strip()
        if hall_entry and hall_entry not in by_key_or_entry:
            by_key_or_entry[hall_entry] = entry
        hall_plain = str(entry.get("hall") or "").strip()
        if hall_plain and hall_plain not in by_key_or_entry:
            by_key_or_entry[hall_plain] = entry

    for hall_key, entry in data.items():
        alias_keys = _as_alias_keys(entry.get("hall_aliases"))
        if not alias_keys:
            continue

        aliases_plain: List[str] = []
        aliases_latex: List[str] = []
        aliases_html: List[str] = []
        aliases_unicode: List[str] = []
        seen: set[str] = set()

        for alias_key in alias_keys:
            if alias_key == hall_key or alias_key in seen:
                continue
            seen.add(alias_key)

            alias_entry = by_key_or_entry.get(alias_key) or {}
            alias_plain = _first_non_empty(alias_entry.get("hall"), alias_key)
            alias_latex = _first_non_empty(alias_entry.get("hall_latex"))
            alias_html = _first_non_empty(alias_entry.get("hall_html"), alias_entry.get("hall_unicode"), alias_plain)
            alias_unicode = _first_non_empty(alias_entry.get("hall_unicode"), alias_plain)

            aliases_plain.append(str(alias_plain))
            if alias_latex is not None:
                aliases_latex.append(str(alias_latex))
            if alias_html is not None:
                aliases_html.append(str(alias_html))
            aliases_unicode.append(str(alias_unicode))

        if not aliases_plain:
            continue

        entry["hall_aliases"] = aliases_plain
        entry["hall_aliases_unicode"] = entry.get("hall_aliases_unicode") if entry.get("hall_aliases_unicode") else aliases_unicode
        if entry.get("hall_aliases_latex") is None:
            if len(aliases_latex) == len(aliases_plain):
                entry["hall_aliases_latex"] = aliases_latex
            else:
                entry["hall_aliases_latex"] = None
        if not entry.get("hall_aliases_html"):
            if len(aliases_html) == len(aliases_plain):
                entry["hall_aliases_html"] = aliases_html
            else:
                entry["hall_aliases_html"] = None


def load_data() -> Dict[str, Dict[str, Any]]:
    _log(f"Loading symmetry basics from {_resolve_input_path(SYMMETRY_BASICS_PATH)}")
    payload = _load_json(SYMMETRY_BASICS_PATH)

    raw_data = _pick_dataset(payload, "spacegroups")

    normalized: Dict[str, Dict[str, Any]] = {}
    if isinstance(raw_data, list):
        index = payload.get("indicies", {}).get("index_hall_entry_to_spacegroups") if isinstance(payload.get("indicies"), dict) else None
        if isinstance(index, dict):
            ordered = sorted(index.items(), key=lambda item: item[1] if isinstance(item[1], int) else 10**9)
            for raw_hall_key, pos in ordered:
                if not isinstance(pos, int) or pos < 0 or pos >= len(raw_data):
                    continue
                hall_key = str(raw_hall_key)
                normalized[hall_key] = _normalize_entry(hall_key, raw_data[pos])
        else:
            for raw_entry in raw_data:
                if not isinstance(raw_entry, dict):
                    continue
                hall_key = str(_first_non_empty(raw_entry.get("hall_entry"), raw_entry.get("hall"), len(normalized)))
                normalized[hall_key] = _normalize_entry(hall_key, raw_entry)
    elif isinstance(raw_data, dict):
        for raw_hall_key, raw_entry in raw_data.items():
            hall_key = str(raw_hall_key)
            normalized[hall_key] = _normalize_entry(hall_key, raw_entry)
    else:
        raise TypeError("Expected symmetry basics spacegroups payload to be a list or object")
    attach_hall_aliases(normalized)
    return normalized


def _normalize_pointgroup_entry(pointgroup_key: str, raw_entry: Any) -> Dict[str, Any]:
    entry = dict(raw_entry) if isinstance(raw_entry, dict) else {}
    normalized = dict(entry)

    normalized["pointgroup_key"] = pointgroup_key
    normalized["hm_symbol"] = _first_non_empty(entry.get("hm_symbol"), pointgroup_key)
    normalized["crystal_system"] = _first_non_empty(entry.get("crystal_system"))
    normalized["laue_class"] = _first_non_empty(entry.get("laue_class"))
    normalized["schoenflies"] = _first_non_empty(entry.get("schoenflies"))
    normalized["schoenflies_latex"] = _first_non_empty(_markup(entry, "schoenflies", "latex"), entry.get("schoenflies_latex"))
    normalized["schoenflies_html"] = _normalize_schoenflies_html(
        _first_non_empty(_markup(entry, "schoenflies", "html"), entry.get("schoenflies_html"), normalized["schoenflies"])
    )
    normalized["schoenflies_unicode"] = _first_non_empty(_markup(entry, "schoenflies", "unicode"), entry.get("schoenflies_unicode"), normalized["schoenflies"])

    raw_symops = entry.get("symops") if isinstance(entry.get("symops"), list) else []
    symops: List[Dict[str, Any]] = []
    for raw_op in raw_symops:
        if not isinstance(raw_op, dict):
            continue
        op = _normalize_op(raw_op)
        det = op.get("P_det")
        if op.get("is_proper") is None and isinstance(det, int):
            op["is_proper"] = det > 0
        symops.append(op)
    normalized["symops"] = symops

    conjugacy = entry.get("conjugacy_classes")
    normalized["conjugacy_classes"] = conjugacy if isinstance(conjugacy, list) else []

    character_real = entry.get("character_table_real")
    normalized["character_table_real"] = character_real if isinstance(character_real, list) else []

    character_complex = entry.get("character_table_complex")
    normalized["character_table_complex"] = character_complex if isinstance(character_complex, list) else []

    return normalized


def load_pointgroup_data() -> Dict[str, Dict[str, Any]]:
    _log(f"Loading pointgroup basics from {_resolve_input_path(SYMMETRY_BASICS_PATH)}")
    payload = _load_json(SYMMETRY_BASICS_PATH)
    raw_data = _pick_dataset(payload, "pointgroups")

    if isinstance(raw_data, list):
        normalized: Dict[str, Dict[str, Any]] = {}
        for raw_entry in raw_data:
            if not isinstance(raw_entry, dict):
                continue
            pointgroup_key = str(_first_non_empty(raw_entry.get("hm_symbol"), len(normalized)))
            normalized[pointgroup_key] = _normalize_pointgroup_entry(pointgroup_key, raw_entry)
        return normalized

    if not _looks_like_pointgroup_map(raw_data):
        return {}

    normalized: Dict[str, Dict[str, Any]] = {}
    for raw_key, raw_entry in raw_data.items():
        pointgroup_key = str(raw_key)
        normalized[pointgroup_key] = _normalize_pointgroup_entry(pointgroup_key, raw_entry)
    return normalized


def _pointgroup_slug_base(symbol: str) -> str:
    text = str(symbol).strip().lower()
    if text.startswith("-"):
        text = f"neg-{text[1:]}"
    text = text.replace("/", "-over-")
    text = text.replace("*", "star")
    text = text.replace('"', "prime")
    text = text.replace(" ", "-")
    text = re.sub(r"[^a-z0-9-]", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "pointgroup"


def attach_pointgroup_slugs(pointgroup_data: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    used_slugs: set[str] = set()
    symbol_to_slug: Dict[str, str] = {}

    for pointgroup_key in sorted(pointgroup_data.keys()):
        base_slug = _pointgroup_slug_base(pointgroup_key)
        slug = base_slug
        suffix = 2
        while slug in used_slugs:
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        used_slugs.add(slug)
        symbol_to_slug[pointgroup_key] = slug

    lookup: Dict[str, str] = {}
    for pointgroup_key, entry in pointgroup_data.items():
        slug = symbol_to_slug[pointgroup_key]
        entry["slug"] = slug
        entry["url"] = f"/pointgroup/{slug}/"

        key_text = str(pointgroup_key).strip()
        if key_text:
            lookup[key_text] = slug

        hm_symbol = str(entry.get("hm_symbol") or "").strip()
        if hm_symbol:
            lookup[hm_symbol] = slug

    return lookup


def build_pointgroup_index_rows(pointgroup_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for pointgroup_key, entry in pointgroup_data.items():
        rows.append(
            {
                "pointgroup_key": pointgroup_key,
                "slug": entry.get("slug"),
                "hm_symbol": entry.get("hm_symbol"),
                "schoenflies": entry.get("schoenflies"),
                "schoenflies_latex": entry.get("schoenflies_latex"),
                "schoenflies_html": entry.get("schoenflies_html"),
                "schoenflies_unicode": entry.get("schoenflies_unicode"),
                "crystal_system": entry.get("crystal_system"),
                "laue_class": entry.get("laue_class"),
                "order": entry.get("order"),
                "n_conjugacy_classes": entry.get("n_conjugacy_classes"),
                "is_centrosymmetric": bool(entry.get("is_centrosymmetric")),
            }
        )

    rows.sort(
        key=lambda item: (
            str(item.get("crystal_system") or ""),
            item.get("order") if isinstance(item.get("order"), int) else 10**9,
            str(item.get("hm_symbol") or item.get("pointgroup_key") or ""),
        )
    )
    return rows


def build_pointgroup_nav_rows(pointgroup_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for pointgroup_key, entry in pointgroup_data.items():
        rows.append(
            {
                "pointgroup_key": pointgroup_key,
                "slug": entry.get("slug"),
                "hm_symbol": entry.get("hm_symbol"),
                "schoenflies_unicode": entry.get("schoenflies_unicode"),
                "crystal_system": entry.get("crystal_system"),
                "order": entry.get("order"),
            }
        )

    rows.sort(
        key=lambda item: (
            str(item.get("crystal_system") or ""),
            item.get("order") if isinstance(item.get("order"), int) else 10**9,
            str(item.get("hm_symbol") or item.get("pointgroup_key") or ""),
        )
    )
    return rows


def load_barnighausen_data() -> Dict[str, Dict[str, Dict[str, Any]]]:
    transformations = _load_transformations_payload()
    rows = _unwrap_data_list(transformations, "transformations_per_hm_entry")
    result: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        source = str(row.get("hall_entry") or "").strip()
        if not source:
            continue
        for group in row.get("baernighausen") or []:
            if not isinstance(group, dict):
                continue
            target = str(group.get("target_hall_entry") or "").strip()
            if not target:
                continue
            transforms = []
            for transform in group.get("transforms") or []:
                if isinstance(transform, dict):
                    transforms.append(_normalize_affine_record(transform))
            if transforms:
                result.setdefault(source, {}).setdefault(target, []).extend(transforms)
    if not result:
        _log("Baernighausen data not found; subgroup mapping tables will be empty")
    return result


def load_euclidian_normalizer_data() -> Dict[str, Dict[str, Any]]:
    transformations = _load_transformations_payload()
    result: Dict[str, Dict[str, Any]] = {}
    for row in _unwrap_data_list(transformations, "transformations_per_hm_entry"):
        hall_key = str(row.get("hall_entry") or "").strip()
        payload = row.get("euclidean_normalizer")
        if hall_key and isinstance(payload, dict) and hall_key not in result:
            normalized = _normalize_normalizer_payload(payload)
            normalized["centering_translations"] = _first_non_empty(row.get("centering_translations"))
            normalized["centering_translations_xyz"] = _first_non_empty(
                row.get("centering_translations_xyz"),
                _centering_translations_xyz(row),
            )
            result[hall_key] = normalized
    if not result:
        _log("Euclidean normalizer data not found; discrete Euclidean normalizer section will be empty")
    return result


def load_continuous_euclidian_normalizer_data() -> Dict[str, Dict[str, Any]]:
    transformations = _load_transformations_payload()
    result: Dict[str, Dict[str, Any]] = {}
    for row in _unwrap_data_list(transformations, "transformations_per_hm_entry"):
        hall_key = str(row.get("hall_entry") or "").strip()
        payload = row.get("continuous_normalizer")
        if hall_key and isinstance(payload, dict) and hall_key not in result:
            result[hall_key] = payload
    if not result:
        _log("Continuous normalizer data not found; continuous normalizer note box will be empty")
    return result


def load_affine_normalizer_data() -> Dict[str, Dict[str, Any]]:
    transformations = _load_transformations_payload()
    result: Dict[str, Dict[str, Any]] = {}
    for row in _unwrap_data_list(transformations, "transformations_per_hm_entry"):
        hall_key = str(row.get("hall_entry") or "").strip()
        payload = row.get("affine_normalizer")
        if hall_key and isinstance(payload, dict) and hall_key not in result:
            result[hall_key] = _normalize_normalizer_payload(payload)
    if not result:
        _log("Affine normalizer data not found; discrete affine normalizer section will be empty")
    return result


def load_cell_commensurator_data() -> Dict[str, Dict[str, Any]]:
    transformations = _load_transformations_payload()
    result: Dict[str, Dict[str, Any]] = {}
    for row in _unwrap_data_list(transformations, "transformations_per_hm_entry"):
        hall_key = str(row.get("hall_entry") or "").strip()
        payload = row.get("isomorphic_subgroups")
        if hall_key and isinstance(payload, dict) and hall_key not in result:
            result[hall_key] = {"items": [_normalize_affine_record(item) for item in payload.get("items") or [] if isinstance(item, dict)]}
    if not result:
        _log("Isomorphic subgroup data not found; Isomorphic Subgroups section will be empty")
    return result


def load_std_setting_transform_data() -> Dict[str, Dict[str, Any]]:
    """Hall-entry keyed exact transforms to the IT-standard Hall setting.

    Reads ``hall_to_it_std_transform`` whose embedded affine map follows the
    convention ``x_setting = matrix * x_std + vector`` (standard -> setting).
    """
    transformations = _load_transformations_payload()
    result: Dict[str, Dict[str, Any]] = {}
    for row in _unwrap_data_list(transformations, "transformations_per_hm_entry"):
        hall_key = str(row.get("hall_entry") or "").strip()
        payload = row.get("hall_to_it_std_transform")
        if not hall_key or not isinstance(payload, dict) or hall_key in result:
            continue
        affine = payload.get("affine_transformation")
        if not isinstance(affine, dict):
            continue
        result[hall_key] = {
            "matrix": affine.get("matrix"),
            "vector": affine.get("vector"),
            "to_hall_entry": _first_non_empty(payload.get("to_hall_entry"), payload.get("to_hall")),
        }
    if not result:
        _log("hall_to_it_std_transform data not found; Setting Transformations section will be empty")
    return result


def build_setting_transforms(
    related_settings: Dict[str, List[Dict[str, Any]]],
    std_transform_data: Dict[str, Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """For each setting, the composed exact transform to every sibling setting.

    Siblings are the other Hall settings sharing the same ITA number (taken
    from ``related_settings``). The current setting is omitted from its own
    list. Each item carries the target setting's labels plus the composed
    ``x_target = P * x_source + p`` transform.
    """
    result: Dict[str, List[Dict[str, Any]]] = {}
    for hall_key, siblings in related_settings.items():
        source_std = std_transform_data.get(hall_key)
        items: List[Dict[str, Any]] = []
        for sibling in siblings:
            target_key = sibling.get("hall_key")
            if not target_key or target_key == hall_key:
                continue
            transform = _compose_setting_transform(source_std, std_transform_data.get(target_key))
            if transform is None:
                continue
            item = {
                "hall_key": target_key,
                "hall_entry": sibling.get("hall_entry"),
                "hall_latex": sibling.get("hall_latex"),
                "hall_html": sibling.get("hall_html"),
                "hall_unicode": sibling.get("hall_unicode"),
                "hm_short": sibling.get("hm_short"),
                "hm_short_latex": sibling.get("hm_short_latex"),
                "hm_short_html": sibling.get("hm_short_html"),
                "hm_short_unicode": sibling.get("hm_short_unicode"),
                "setting": sibling.get("setting"),
                "qualifier": sibling.get("qualifier"),
                "is_reference_setting": bool(sibling.get("is_reference_setting")),
            }
            item.update(transform)
            items.append(item)
        if items:
            result[hall_key] = items
    if not result:
        _log("No sibling setting transforms could be composed; Setting Transformations section will be empty")
    return result


def choose_standard_setting(entries: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not entries:
        return None
    for entry in entries:
        if entry.get("is_reference_setting"):
            return entry
    return entries[0]


def build_index_rows(data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for hall_key, entry in data.items():
        row = {"hall_key": hall_key}
        for field in INDEX_FIELDS:
            if field == "hall_key":
                continue
            row[field] = entry.get(field)
        rows.append(row)

    return sorted(
        rows,
        key=lambda item: (
            item.get("ita_number") if item.get("ita_number") is not None else 0,
            item.get("hall_key", ""),
        ),
    )


def build_related_settings(
    index_rows: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    by_ita: Dict[int, List[Dict[str, Any]]] = {}
    for row in index_rows:
        ita = row.get("ita_number")
        if ita is None:
            continue
        by_ita.setdefault(int(ita), []).append(row)

    related: Dict[str, List[Dict[str, Any]]] = {}
    for ita, rows in by_ita.items():
        group = sorted(
            rows,
            key=lambda item: (
                0 if item.get("is_reference_setting") else 1,
                str(item.get("qualifier") or ""),
                item["hall_key"],
            ),
        )
        for row in group:
            related[row["hall_key"]] = [
                {
                    "hall_key": item["hall_key"],
                    "hall_entry": item.get("hall_entry"),
                    "hall_latex": item.get("hall_latex"),
                    "hall_html": item.get("hall_html"),
                    "hall_unicode": item.get("hall_unicode"),
                    "qualifier": item.get("qualifier"),
                    "setting": item.get("setting"),
                    "hm_short": _first_non_empty(item.get("hm_short"), item.get("hm_full"), item.get("hm_universal")),
                    "hm_short_latex": item.get("hm_short_latex"),
                    "hm_short_html": _first_non_empty(item.get("hm_short_html"), item.get("hm_full_html"), item.get("hm_short")),
                    "hm_short_unicode": _first_non_empty(item.get("hm_short_unicode"), item.get("hm_full_unicode"), item.get("hm_short")),
                    "hm_short_aliases": _first_non_empty(item.get("hm_short_aliases")),
                    "hm_short_aliases_latex": item.get("hm_short_aliases_latex"),
                    "hm_short_aliases_html": _first_non_empty(item.get("hm_short_aliases_html"), item.get("hm_short_aliases")),
                    "hm_short_aliases_unicode": _first_non_empty(item.get("hm_short_aliases_unicode"), item.get("hm_short_aliases")),
                    "hm_universal": _first_non_empty(item.get("hm_universal"), item.get("hm_extended"), item.get("hm_full")),
                    "hm_universal_latex": item.get("hm_universal_latex"),
                    "hm_universal_html": _first_non_empty(item.get("hm_universal_html"), item.get("hm_extended_html"), item.get("hm_universal")),
                    "hm_universal_unicode": _first_non_empty(
                        item.get("hm_universal_unicode"), item.get("hm_extended_unicode"), item.get("hm_universal")
                    ),
                    "is_reference_setting": bool(item.get("is_reference_setting")),
                }
                for item in group
            ]
    return related


def _mapping_with_target_metadata(
    target_hall_key: str,
    mapping: Dict[str, Any],
    data: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    target = data.get(target_hall_key, {})
    return {
        "hall_key": target_hall_key,
        "hall_entry": target.get("hall_entry"),
        "hall_latex": target.get("hall_latex"),
        "hall_html": target.get("hall_html"),
        "hall_unicode": target.get("hall_unicode"),
        "hm_short": _first_non_empty(target.get("hm_short"), target.get("hm_full"), target.get("hm_universal")),
        "hm_short_aliases": _first_non_empty(target.get("hm_short_aliases")),
        "hm_short_aliases_latex": target.get("hm_short_aliases_latex"),
        "hm_short_aliases_html": _first_non_empty(target.get("hm_short_aliases_html"), target.get("hm_short_aliases")),
        "hm_short_aliases_unicode": _first_non_empty(target.get("hm_short_aliases_unicode"), target.get("hm_short_aliases")),
        "hm_short_latex": target.get("hm_short_latex"),
        "hm_short_html": _first_non_empty(target.get("hm_short_html"), target.get("hm_full_html"), target.get("hm_short")),
        "hm_short_unicode": _first_non_empty(
            target.get("hm_short_unicode"), target.get("hm_full_unicode"), target.get("hm_short")
        ),
        "hm_full": _first_non_empty(target.get("hm_full"), target.get("hm_short")),
        "hm_full_latex": target.get("hm_full_latex"),
        "hm_full_html": _first_non_empty(target.get("hm_full_html"), target.get("hm_short_html"), target.get("hm_full")),
        "hm_full_unicode": _first_non_empty(target.get("hm_full_unicode"), target.get("hm_short_unicode"), target.get("hm_full")),
        "hm_extended": _first_non_empty(target.get("hm_extended"), target.get("hm_full")),
        "hm_extended_latex": target.get("hm_extended_latex"),
        "hm_extended_html": _first_non_empty(target.get("hm_extended_html"), target.get("hm_full_html"), target.get("hm_extended")),
        "hm_extended_unicode": _first_non_empty(target.get("hm_extended_unicode"), target.get("hm_full_unicode"), target.get("hm_extended")),
        "hm_universal": _first_non_empty(target.get("hm_universal"), target.get("hm_extended"), target.get("hm_full")),
        "hm_universal_aliases": _first_non_empty(target.get("hm_universal_aliases")),
        "hm_universal_aliases_latex": target.get("hm_universal_aliases_latex"),
        "hm_universal_aliases_html": _first_non_empty(target.get("hm_universal_aliases_html"), target.get("hm_universal_aliases")),
        "hm_universal_aliases_unicode": _first_non_empty(
            target.get("hm_universal_aliases_unicode"), target.get("hm_universal_aliases")
        ),
        "hm_universal_latex": target.get("hm_universal_latex"),
        "hm_universal_html": _first_non_empty(target.get("hm_universal_html"), target.get("hm_extended_html"), target.get("hm_universal")),
        "hm_universal_unicode": _first_non_empty(
            target.get("hm_universal_unicode"), target.get("hm_extended_unicode"), target.get("hm_universal")
        ),
        "qualifier": target.get("qualifier"),
        "point_group": target.get("point_group"),
        "schoenflies": target.get("schoenflies"),
        "schoenflies_latex": target.get("schoenflies_latex"),
        "schoenflies_html": target.get("schoenflies_html"),
        "schoenflies_unicode": target.get("schoenflies_unicode"),
        "ita_number": target.get("ita_number"),
        "is_reference_setting": bool(target.get("is_reference_setting")),
        "index": mapping.get("index"),
        "transformation_matrix": mapping.get("transformation_matrix"),
        "origin_shift": mapping.get("origin_shift"),
        "centering_translations_xyz": _first_non_empty(
            mapping.get("h_centering_translations_xyz"),
            target.get("centering_translations_xyz"),
        ),
        "wyckoff_rows": mapping.get("wyckoff_rows"),
    }


def _parse_fraction(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, float):
        return Fraction(value).limit_denominator(144)
    text = str(value).strip()
    if not text:
        return Fraction(0, 1)
    return Fraction(text)


def _fraction_to_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _format_affine_expression(row: List[Any]) -> str:
    coeffs = [_parse_fraction(v) for v in row[:3]]
    shift = _parse_fraction(row[3] if len(row) > 3 else 0)
    vars_ = ["x", "y", "z"]
    terms: List[str] = []

    for coeff, var in zip(coeffs, vars_):
        if coeff == 0:
            continue
        if coeff == 1:
            terms.append(var)
        elif coeff == -1:
            terms.append(f"-{var}")
        else:
            terms.append(f"{_fraction_to_text(coeff)}*{var}")

    expr = " + ".join(terms) if terms else "0"
    expr = expr.replace("+ -", "- ")

    if shift != 0:
        if shift > 0:
            expr = f"{expr} + {_fraction_to_text(shift)}"
        else:
            expr = f"{expr} - {_fraction_to_text(abs(shift))}"
    return expr


def _matrix3_fractions(matrix: Any) -> List[List[Fraction]] | None:
    if not isinstance(matrix, list) or len(matrix) < 3:
        return None
    rows: List[List[Fraction]] = []
    for raw_row in matrix[:3]:
        if not isinstance(raw_row, list) or len(raw_row) < 3:
            return None
        rows.append([_parse_fraction(value) for value in raw_row[:3]])
    return rows


def _vector3_fractions(vector: Any) -> List[Fraction]:
    values = vector[:3] if isinstance(vector, list) else []
    out = [_parse_fraction(value) for value in values]
    while len(out) < 3:
        out.append(Fraction(0))
    return out


def _matrix3_inverse(matrix: List[List[Fraction]]) -> List[List[Fraction]] | None:
    (a, b, c), (d, e, f), (g, h, i) = matrix
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if det == 0:
        return None
    cof = [
        [(e * i - f * h), -(b * i - c * h), (b * f - c * e)],
        [-(d * i - f * g), (a * i - c * g), -(a * f - c * d)],
        [(d * h - e * g), -(a * h - b * g), (a * e - b * d)],
    ]
    return [[cof[r][col] / det for col in range(3)] for r in range(3)]


def _matrix3_matmul(left: List[List[Fraction]], right: List[List[Fraction]]) -> List[List[Fraction]]:
    return [[sum(left[r][k] * right[k][col] for k in range(3)) for col in range(3)] for r in range(3)]


def _matrix3_matvec(matrix: List[List[Fraction]], vector: List[Fraction]) -> List[Fraction]:
    return [sum(matrix[r][k] * vector[k] for k in range(3)) for r in range(3)]


def _compose_setting_transform(
    source_std: Dict[str, Any] | None,
    target_std: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    """Compose the exact transform from the source setting A to the target B.

    Both inputs are the stored ``hall_to_it_std_transform`` records, whose
    convention is ``x_setting = P * x_std + p`` (standard -> setting). The
    composed transform satisfies ``x_B = P_AB * x_A + p_AB`` with
    ``P_AB = P_B * P_A^-1`` and ``p_AB = p_B - P_AB * p_A``.
    """
    if not isinstance(source_std, dict) or not isinstance(target_std, dict):
        return None
    p_a = _matrix3_fractions(source_std.get("matrix"))
    p_b = _matrix3_fractions(target_std.get("matrix"))
    if p_a is None or p_b is None:
        return None
    p_a_inv = _matrix3_inverse(p_a)
    if p_a_inv is None:
        return None
    matrix = _matrix3_matmul(p_b, p_a_inv)
    shift_a = _vector3_fractions(source_std.get("vector"))
    shift_b = _vector3_fractions(target_std.get("vector"))
    shift = [shift_b[r] - val for r, val in enumerate(_matrix3_matvec(matrix, shift_a))]
    matrix_text = [[_fraction_to_text(value) for value in row] for row in matrix]
    shift_text = [_fraction_to_text(value) for value in shift]
    algebraic = [
        _format_affine_expression(matrix_text[r] + [shift_text[r]])
        for r in range(3)
    ]
    return {
        "transformation_matrix": matrix_text,
        "origin_shift": shift_text,
        "transformation_matrix_text": "; ".join(_format_vector_text(row) for row in matrix_text),
        "origin_shift_text": _format_vector_text(shift_text),
        "algebraic_xyz": algebraic,
    }


def _build_wyckoff_multiplicity_map(entry: Dict[str, Any] | None) -> Dict[str, str]:
    if not isinstance(entry, dict):
        return {}
    wyckoff = entry.get("wyckoff")
    if isinstance(wyckoff, list):
        result: Dict[str, str] = {}
        for payload in wyckoff:
            if not isinstance(payload, dict):
                continue
            label = payload.get("letter")
            multiplicity = payload.get("multiplicity")
            if label is not None and multiplicity is not None:
                result[str(label).strip()] = str(multiplicity).strip()
        return result
    if not isinstance(wyckoff, dict):
        return {}

    multiplicity_by_label: Dict[str, str] = {}
    for label, payload in wyckoff.items():
        if not isinstance(payload, dict):
            continue
        multiplicity = payload.get("multiplicity")
        if multiplicity is None:
            continue
        label_text = str(label).strip()
        multiplicity_text = str(multiplicity).strip()
        if not label_text or not multiplicity_text:
            continue
        multiplicity_by_label[label_text] = multiplicity_text
    return multiplicity_by_label


def _wyckoff_lookup_label(label: Any) -> str:
    label_text = str(label).strip()
    return re.sub(r"^\d+", "", label_text)


def _orbit_xyz_list(orbit: Any) -> List[str]:
    if not isinstance(orbit, list):
        return []
    out: List[str] = []
    for item in orbit:
        if isinstance(item, dict) and item.get("xyz") is not None:
            out.append(str(item["xyz"]))
    return out


def _build_wyckoff_orbit_mod_map(entry: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(entry, dict):
        return {}
    wyckoff = entry.get("wyckoff")
    if isinstance(wyckoff, list):
        result: Dict[str, Any] = {}
        for payload in wyckoff:
            if not isinstance(payload, dict):
                continue
            label = payload.get("letter")
            orbit = _first_non_empty(
                _orbit_xyz_list(payload.get("orbit_mod_centering")),
                _orbit_xyz_list(payload.get("orbit")),
            )
            if label is not None and orbit:
                result[_wyckoff_lookup_label(label)] = orbit
        return result
    if not isinstance(wyckoff, dict):
        return {}

    result: Dict[str, Any] = {}
    for label, payload in wyckoff.items():
        if not isinstance(payload, dict):
            continue
        orbit = _first_non_empty(
            _orbit_xyz_list(payload.get("orbit_mod_centering")),
            _orbit_xyz_list(payload.get("orbit")),
        )
        if orbit:
            result[_wyckoff_lookup_label(label)] = orbit
    return result


def _format_wyckoff_label(label: Any, multiplicity_by_label: Dict[str, str]) -> str:
    label_text = str(label).strip()
    if not label_text:
        return ""
    if label_text[:1].isdigit():
        return label_text
    multiplicity = multiplicity_by_label.get(label_text)
    if not multiplicity:
        return label_text
    return f"{multiplicity}{label_text}"


def _annotate_wyckoff_group_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    annotated = [dict(row) for row in rows]
    idx = 0
    total = len(annotated)
    while idx < total:
        group_key = str(annotated[idx].get("g_wp", ""))
        end = idx + 1
        while end < total and str(annotated[end].get("g_wp", "")) == group_key:
            end += 1
        rowspan = end - idx
        annotated[idx]["g_wp_show"] = True
        annotated[idx]["g_wp_rowspan"] = rowspan
        for j in range(idx + 1, end):
            annotated[j]["g_wp_show"] = False
            annotated[j]["g_wp_rowspan"] = 0
        idx = end
    return annotated


def _build_wyckoff_rows(
    mapping: Dict[str, Any],
    g_multiplicity_by_label: Dict[str, str] | None = None,
    h_multiplicity_by_label: Dict[str, str] | None = None,
    h_orbit_mod_by_label: Dict[str, Any] | None = None,
    h_centering_translations_xyz: Any = None,
) -> List[Dict[str, Any]]:
    g_mult = g_multiplicity_by_label or {}
    h_mult = h_multiplicity_by_label or {}
    h_orbit_mod = h_orbit_mod_by_label or {}
    wyckoff = mapping.get("wyckoff_splitting")
    if isinstance(wyckoff, list):
        rows: List[Dict[str, Any]] = []
        for group in wyckoff:
            if not isinstance(group, dict):
                continue
            g_wp = group.get("parent")
            splits = group.get("splits")
            if not isinstance(splits, list):
                continue
            for split in splits:
                if not isinstance(split, dict):
                    continue
                h_wp = split.get("letter")
                h_first_orbit = split.get("xyz")
                affine = split.get("affine") if isinstance(split.get("affine"), list) else []
                affine_xyz = []
                for affine_row in affine[:3]:
                    if isinstance(affine_row, list):
                        affine_xyz.append(_format_affine_expression(affine_row))
                rows.append(
                    {
                        "g_wp": g_wp,
                        "g_wp_display": _format_wyckoff_label(g_wp, g_mult),
                        "h_wp": h_wp,
                        "h_wp_display": _format_wyckoff_label(h_wp, h_mult),
                        "h_first_orbit_xyz": h_first_orbit,
                        "h_orbit_mod_centering_xyz": _first_non_empty(
                            h_orbit_mod.get(_wyckoff_lookup_label(h_wp)),
                            h_first_orbit,
                        ),
                        "h_centering_translations_xyz": h_centering_translations_xyz,
                        "affine_xyz": affine_xyz,
                    }
                )
        rows.sort(key=lambda item: (str(item.get("g_wp", "")), str(item.get("h_wp", "")), str(item.get("h_first_orbit_xyz", ""))))
        return _annotate_wyckoff_group_rows(rows)

    if not isinstance(wyckoff, dict):
        return []

    rows: List[Dict[str, Any]] = []
    for g_wp, splits in wyckoff.items():
        if not isinstance(splits, list):
            continue
        for split in splits:
            if not isinstance(split, list) or len(split) < 3:
                continue
            h_wp = split[0]
            h_first_orbit = split[1]
            affine = split[2] if isinstance(split[2], list) else []
            affine_xyz = []
            if isinstance(affine, list):
                for affine_row in affine[:3]:
                    if isinstance(affine_row, list):
                        affine_xyz.append(_format_affine_expression(affine_row))
            rows.append(
                {
                    "g_wp": g_wp,
                    "g_wp_display": _format_wyckoff_label(g_wp, g_mult),
                "h_wp": h_wp,
                "h_wp_display": _format_wyckoff_label(h_wp, h_mult),
                "h_first_orbit_xyz": h_first_orbit,
                "h_orbit_mod_centering_xyz": _first_non_empty(
                    h_orbit_mod.get(_wyckoff_lookup_label(h_wp)),
                    h_first_orbit,
                ),
                "h_centering_translations_xyz": h_centering_translations_xyz,
                "affine_xyz": affine_xyz,
            }
        )

    rows.sort(key=lambda item: (str(item.get("g_wp", "")), str(item.get("h_wp", "")), str(item.get("h_first_orbit_xyz", ""))))
    return _annotate_wyckoff_group_rows(rows)


def _build_wyckoff_items(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    wyckoff = entry.get("wyckoff")
    if isinstance(wyckoff, list):
        items = []
        for payload in wyckoff:
            if not isinstance(payload, dict):
                continue
            items.append(
                {
                    "label": payload.get("letter"),
                    "multiplicity": payload.get("multiplicity"),
                    "sitesym": payload.get("sitesym"),
                    "orbit_xyz": _orbit_xyz_list(payload.get("orbit")),
                    "orbit_mod_centering_xyz": _orbit_xyz_list(payload.get("orbit_mod_centering")),
                }
            )
        items.sort(key=lambda item: (not str(item.get("label", "")).islower(), str(item.get("label", "")).lower(), str(item.get("label", ""))))
        return items
    if not isinstance(wyckoff, dict):
        return []

    items: List[Dict[str, Any]] = []
    for label, payload in wyckoff.items():
        if not isinstance(payload, dict):
            continue
        items.append(
            {
                "label": label,
                "multiplicity": payload.get("multiplicity"),
                "sitesym": payload.get("sitesym"),
                "orbit_xyz": _orbit_xyz_list(payload.get("orbit")),
                "orbit_mod_centering_xyz": _orbit_xyz_list(payload.get("orbit_mod_centering")),
            }
        )

    # Keep lowercase labels first; place uppercase labels like "A" after "z".
    items.sort(key=lambda item: (not str(item.get("label", "")).islower(), str(item.get("label", "")).lower(), str(item.get("label", ""))))
    return items


def _format_vector_text(values: List[Any], max_len: int = 3) -> str:
    trimmed = values[:max_len]
    return f"[{', '.join(str(value) for value in trimmed)}]"


def _build_cell_commensurator_items(raw_items: Any, source_entry: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []

    source_mult = _build_wyckoff_multiplicity_map(source_entry)
    source_orbit_mod = _build_wyckoff_orbit_mod_map(source_entry)
    source_centering_translations_xyz = (
        source_entry.get("centering_translations_xyz") if isinstance(source_entry, dict) else None
    )

    items: List[Dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue

        index = raw.get("index")
        if not isinstance(index, int):
            try:
                index = int(index)
            except (TypeError, ValueError):
                index = None

        matrix = raw.get("transformation_matrix")
        if not isinstance(matrix, list):
            matrix = raw.get("P")
        shift = raw.get("origin_shift")
        if not isinstance(shift, list):
            shift = raw.get("p")

        matrix_rows = [row for row in matrix[:3] if isinstance(row, list)] if isinstance(matrix, list) else []
        shift_values = shift[:3] if isinstance(shift, list) else []

        wyckoff_rows = _build_wyckoff_rows(
            raw,
            source_mult,
            source_mult,
            source_orbit_mod,
            source_centering_translations_xyz,
        )
        items.append(
            {
                "index": index,
                "transformation_matrix": matrix_rows,
                "origin_shift": shift_values,
                "transformation_matrix_text": "; ".join(_format_vector_text(row) for row in matrix_rows) if matrix_rows else None,
                "origin_shift_text": _format_vector_text(shift_values) if shift_values else None,
                "wyckoff_rows": wyckoff_rows,
                "centering_translations_xyz": source_centering_translations_xyz,
                # Cell commensurator relations are self-relations for the current Hall setting.
                "is_reference_setting": True,
            }
        )

    items.sort(
        key=lambda item: (
            item.get("index") if item.get("index") is not None else 10**9,
            str(item.get("transformation_matrix_text") or ""),
            str(item.get("origin_shift_text") or ""),
        )
    )
    return items


def build_group_mappings(
    data: Dict[str, Dict[str, Any]],
    barnighausen: Dict[str, Dict[str, Any]],
) -> tuple[
    Dict[str, List[Dict[str, Any]]],
    Dict[str, List[Dict[str, Any]]],
]:
    outgoing: Dict[str, List[tuple[str, Dict[str, Any]]]] = {}
    incoming: Dict[str, List[tuple[str, Dict[str, Any]]]] = {}
    wyckoff_mult_by_hall = {hall_key: _build_wyckoff_multiplicity_map(entry) for hall_key, entry in data.items()}
    wyckoff_orbit_mod_by_hall = {hall_key: _build_wyckoff_orbit_mod_map(entry) for hall_key, entry in data.items()}

    for g_hall, targets in barnighausen.items():
        if not isinstance(targets, dict):
            continue
        for h_hall, raw_mapping in targets.items():
            candidates = raw_mapping if isinstance(raw_mapping, list) else [raw_mapping]
            for mapping in candidates:
                if not isinstance(mapping, dict):
                    continue
                index = mapping.get("index")
                if not isinstance(index, int):
                    try:
                        index = int(index)
                    except (TypeError, ValueError):
                        continue
                normalized = {
                    "index": index,
                    "transformation_matrix": mapping.get("transformation_matrix"),
                    "origin_shift": mapping.get("origin_shift"),
                    "wyckoff_rows": _build_wyckoff_rows(
                        mapping,
                        wyckoff_mult_by_hall.get(g_hall, {}),
                        wyckoff_mult_by_hall.get(h_hall, {}),
                        wyckoff_orbit_mod_by_hall.get(h_hall, {}),
                        data.get(h_hall, {}).get("centering_translations_xyz"),
                    ),
                    "h_centering_translations_xyz": data.get(h_hall, {}).get("centering_translations_xyz"),
                }
                outgoing.setdefault(g_hall, []).append((h_hall, normalized))
                incoming.setdefault(h_hall, []).append((g_hall, normalized))

    def dedupe_edges(edges: List[tuple[str, Dict[str, Any]]]) -> List[tuple[str, Dict[str, Any]]]:
        by_other: Dict[str, Dict[str, Any]] = {}
        for other_hall, mapping in edges:
            existing = by_other.get(other_hall)
            if existing is None or mapping["index"] < existing["index"]:
                by_other[other_hall] = mapping
        return [(other_hall, by_other[other_hall]) for other_hall in sorted(by_other.keys())]

    def same_ita(hall_key: str, other_hall_key: str) -> bool:
        hall_ita = data.get(hall_key, {}).get("ita_number")
        other_ita = data.get(other_hall_key, {}).get("ita_number")
        if hall_ita is None or other_ita is None:
            return False
        return int(hall_ita) == int(other_ita)

    maximal_subgroup_mappings: Dict[str, List[Dict[str, Any]]] = {}
    minimal_supergroup_mappings: Dict[str, List[Dict[str, Any]]] = {}

    # Same-ITA edges (relations to sibling Hall settings of the same space-group
    # type) are intentionally not surfaced: index-1 edges are pure setting
    # transforms and index>1 edges duplicate the dedicated isomorphic_subgroups
    # dataset field already shown in the Isomorphic Subgroups section. They are
    # only excluded here so they do not leak into maximal/minimal subgroups.
    for hall_key in data:
        out_edges = dedupe_edges(
            [
                (target_hall, mapping)
                for target_hall, mapping in outgoing.get(hall_key, [])
                if not same_ita(hall_key, target_hall)
            ]
        )
        if out_edges:
            selected = [
                _mapping_with_target_metadata(target_hall, mapping, data)
                for target_hall, mapping in out_edges
            ]
            selected.sort(
                key=lambda item: (
                    item.get("ita_number") if isinstance(item.get("ita_number"), int) else 10**9,
                    item.get("index") if isinstance(item.get("index"), int) else 10**9,
                    item["hall_key"],
                )
            )
            maximal_subgroup_mappings[hall_key] = selected
        else:
            maximal_subgroup_mappings[hall_key] = []

        in_edges = dedupe_edges(
            [
                (source_hall, mapping)
                for source_hall, mapping in incoming.get(hall_key, [])
                if not same_ita(hall_key, source_hall)
            ]
        )
        if in_edges:
            selected = [
                _mapping_with_target_metadata(source_hall, mapping, data)
                for source_hall, mapping in in_edges
            ]
            selected.sort(
                key=lambda item: (
                    item.get("ita_number") if isinstance(item.get("ita_number"), int) else 10**9,
                    item.get("index") if isinstance(item.get("index"), int) else 10**9,
                    item["hall_key"],
                )
            )
            minimal_supergroup_mappings[hall_key] = selected
        else:
            minimal_supergroup_mappings[hall_key] = []

    return (
        maximal_subgroup_mappings,
        minimal_supergroup_mappings,
    )


def write_index_data(index_rows: List[Dict[str, Any]]) -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    index_path = DATA_ROOT / "spacegroup_index.json"
    _log(f"Writing index data ({len(index_rows)} rows) to {index_path} and {index_path}.gz")
    index_path.write_text(
        json.dumps(index_rows, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_json_gz(index_path.with_name(f"{index_path.name}.gz"), index_rows)


def write_pointgroup_index_data(pointgroup_index_rows: List[Dict[str, Any]]) -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    index_path = DATA_ROOT / "pointgroup_index.json"
    _log(f"Writing pointgroup index data ({len(pointgroup_index_rows)} rows) to {index_path} and {index_path}.gz")
    index_path.write_text(
        json.dumps(pointgroup_index_rows, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_json_gz(index_path.with_name(f"{index_path.name}.gz"), pointgroup_index_rows)


def write_index_content(index_rows: List[Dict[str, Any]]) -> None:
    CONTENT_ROOT.mkdir(parents=True, exist_ok=True)
    _log(f"Writing index content to {CONTENT_ROOT / '_index.md'}")
    content = """---
title: "Spacegroup Data Explorer"
---
"""

    (CONTENT_ROOT / "_index.md").write_text(content, encoding="utf-8")

    legacy_index = CONTENT_ROOT / "index.md"
    if legacy_index.exists():
        legacy_index.unlink()


def write_pointgroup_index_content() -> None:
    POINTGROUP_ROOT.mkdir(parents=True, exist_ok=True)
    _log(f"Writing pointgroup index content to {POINTGROUP_ROOT / '_index.md'}")
    content = """---
title: "Pointgroup Data Explorer"
---
"""
    (POINTGROUP_ROOT / "_index.md").write_text(content, encoding="utf-8")


def write_pointgroup_pages(
    pointgroup_data: Dict[str, Dict[str, Any]],
    pointgroup_nav: List[Dict[str, Any]],
    field_doc_urls: Dict[str, str],
) -> None:
    POINTGROUP_ROOT.mkdir(parents=True, exist_ok=True)
    total = len(pointgroup_data)
    _log(f"Writing {total} pointgroup detail pages to {POINTGROUP_ROOT}")

    # Sort consistently with the index table.
    ordered = sorted(
        pointgroup_data.items(),
        key=lambda item: (
            str(item[1].get("crystal_system") or ""),
            item[1].get("order") if isinstance(item[1].get("order"), int) else 10**9,
            str(item[1].get("hm_symbol") or item[0]),
        ),
    )
    for idx, (pointgroup_key, entry) in enumerate(ordered, start=1):
        slug = str(entry.get("slug") or pointgroup_key)
        payload: Dict[str, Any] = {
            "title": f"Pointgroup {entry.get('hm_symbol') or pointgroup_key}",
            "pointgroup_key": pointgroup_key,
            "slug": slug,
            "url": f"/pointgroup/{slug}/",
        }
        payload.update(entry)
        payload["pointgroup_nav"] = pointgroup_nav
        payload["field_doc_urls"] = field_doc_urls

        json_text = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
        (POINTGROUP_ROOT / f"{slug}.md").write_text(f"{json_text}\n", encoding="utf-8")
        if idx % 20 == 0 or idx == total:
            _log(f"  wrote {idx}/{total} pointgroup pages")


def _hm_entry_slug(value: Any) -> str:
    """URL slug for an H-M entry: drop spaces and map '/' -> ':' (path-safe)."""
    return str(value or "").strip().replace(" ", "").replace("/", ":")


def build_alias_map(symmetry_basics_payload: Any) -> Dict[str, List[str]]:
    """Map each Hall page to its stable redirect aliases.

    Aliases are built from the authoritative ``symmetry_basics`` indices so the
    sets are exactly right (230 IT numbers, 530 n:c codes, 530 H-M entries),
    each redirecting to the Hall page of the setting it identifies:

    - ``/itn/<it_number>/``           standard (ITA reference) setting per IT number
    - ``/nc/<setting_it_nc>/``        the specific conventional setting (':' kept verbatim)
    - ``/hm/<hm_entry slug>/``        the specific conventional setting, by H-M entry
    """
    indices = symmetry_basics_payload.get("indicies") if isinstance(symmetry_basics_payload, dict) else None
    if not isinstance(indices, dict):
        _log("No 'indicies' in symmetry basics; no /itn//nc//hm/ aliases will be generated")
        return {}

    hall_index = indices.get("index_hall_entry_to_spacegroups")
    if not isinstance(hall_index, dict):
        _log("No index_hall_entry_to_spacegroups; cannot build aliases")
        return {}
    pos_to_hall: Dict[int, str] = {pos: hall for hall, pos in hall_index.items() if isinstance(pos, int)}

    aliases_by_hall: Dict[str, List[str]] = {}
    claimed: Dict[str, str] = {}

    def _add(alias: str, pos: Any) -> None:
        if not isinstance(pos, int):
            return
        hall = pos_to_hall.get(pos)
        if hall is None:
            return
        prior = claimed.get(alias)
        if prior is not None and prior != hall:
            _log(f"Alias collision: {alias} claimed by both {prior} and {hall}")
            return
        claimed[alias] = hall
        aliases_by_hall.setdefault(hall, []).append(alias)

    for it_number, pos in (indices.get("index_it_number_to_std_spacegroups") or {}).items():
        _add(f"/itn/{it_number}/", pos)
    for nc_code, pos in (indices.get("index_setting_it_nc_to_spacegroups") or {}).items():
        _add(f"/nc/{nc_code}/", pos)
    for hm_entry, pos in (indices.get("index_hm_entry_to_spacegroups") or {}).items():
        _add(f"/hm/{_hm_entry_slug(hm_entry)}/", pos)

    for hall in aliases_by_hall:
        aliases_by_hall[hall] = sorted(set(aliases_by_hall[hall]))
    _log(f"Built {len(claimed)} link aliases (itn/nc/hm) across {len(aliases_by_hall)} Hall pages")
    return aliases_by_hall


def write_hall_pages(
    data: Dict[str, Dict[str, Any]],
    field_doc_urls: Dict[str, str],
    aliases_by_hall: Dict[str, List[str]],
    euclidian_normalizer_data: Dict[str, Dict[str, Any]],
    affine_normalizer_data: Dict[str, Dict[str, Any]],
    continuous_euclidian_normalizer_data: Dict[str, Dict[str, Any]],
    cell_commensurator_data: Dict[str, Dict[str, Any]],
    pointgroup_slug_lookup: Dict[str, str],
    related_settings: Dict[str, List[Dict[str, Any]]],
    maximal_subgroup_mappings: Dict[str, List[Dict[str, Any]]],
    minimal_supergroup_mappings: Dict[str, List[Dict[str, Any]]],
    setting_transforms: Dict[str, List[Dict[str, Any]]],
) -> None:
    HALL_ROOT.mkdir(parents=True, exist_ok=True)
    total = len(data)
    _log(f"Writing {total} Hall detail pages to {HALL_ROOT}")

    for idx, (hall_key, entry) in enumerate(data.items(), start=1):
        payload: Dict[str, Any] = {
            "title": f"Spacegroup {hall_key}",
            "hall_key": hall_key,
            "slug": hall_key,
            "url": f"/hall/{hall_key}/",
        }
        payload.update(entry)
        # Stable redirect links (Hugo aliases): /itn/<n>/ (standard setting per
        # IT number), /nc/<n:c>/ and /hm/<H-M entry>/ (the specific conventional
        # setting). Built from the symmetry-basics indices in build_alias_map.
        page_aliases = aliases_by_hall.get(hall_key)
        if page_aliases:
            payload["aliases"] = page_aliases
        payload["field_doc_urls"] = field_doc_urls
        payload["wyckoff_items"] = _build_wyckoff_items(entry)
        payload["related_settings"] = related_settings.get(hall_key, [])
        payload["maximal_subgroup_mappings"] = maximal_subgroup_mappings.get(hall_key, [])
        payload["minimal_supergroup_mappings"] = minimal_supergroup_mappings.get(hall_key, [])
        payload["setting_transforms"] = setting_transforms.get(hall_key, [])
        raw_euclidian = euclidian_normalizer_data.get(hall_key) or {}
        if isinstance(raw_euclidian, dict):
            payload["euclidian_normalizer"] = raw_euclidian.get("euclidian_normalizer", raw_euclidian)
        else:
            payload["euclidian_normalizer"] = None

        raw_affine = affine_normalizer_data.get(hall_key) or {}
        if isinstance(raw_affine, dict):
            payload["affine_normalizer"] = raw_affine.get("affine_normalizer", raw_affine)
        else:
            payload["affine_normalizer"] = None

        raw_continuous = continuous_euclidian_normalizer_data.get(hall_key) or {}
        if isinstance(raw_continuous, dict):
            payload["continuous_euclidian_normalizer"] = raw_continuous.get("continuous_euclidian_normalizer", raw_continuous)
        else:
            payload["continuous_euclidian_normalizer"] = None

        point_group_symbol = str(payload.get("point_group") or "").strip()
        payload["point_group_slug"] = pointgroup_slug_lookup.get(point_group_symbol)
        raw_commensurator = cell_commensurator_data.get(hall_key) or {}
        commensurator_items = (
            _first_non_empty(raw_commensurator.get("items"), raw_commensurator.get("affine_commensurator"))
            if isinstance(raw_commensurator, dict)
            else None
        )
        payload["cell_commensurator"] = _build_cell_commensurator_items(commensurator_items, entry)

        json_text = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
        content = f"{json_text}\n"
        (HALL_ROOT / f"{hall_key}.md").write_text(content, encoding="utf-8")
        if idx % 100 == 0 or idx == total:
            _log(f"  wrote {idx}/{total} pages")


def main() -> None:
    _log("Starting generation")
    symmetry_basics_payload = _load_json(SYMMETRY_BASICS_PATH)
    field_doc_urls = _extract_field_doc_urls(symmetry_basics_payload, ["spacegroups"])
    # The transformations dataset carries its own JSON-LD @context with the
    # OPTIMADE property-definition URLs for the normalizer/subgroup sections.
    field_doc_urls.update(
        _extract_field_doc_urls(_load_transformations_payload(), ["transformations_per_hm_entry"])
    )
    pointgroup_field_doc_urls = _extract_field_doc_urls(symmetry_basics_payload, ["pointgroups"])
    _log(
        f"Loaded {len(field_doc_urls)} spacegroup and {len(pointgroup_field_doc_urls)} pointgroup "
        "field documentation URLs from dataset @context headers"
    )
    data = load_data()
    _log(f"Loaded {len(data)} Hall entries")
    pointgroup_data = load_pointgroup_data()
    _log(f"Loaded pointgroup basics for {len(pointgroup_data)} pointgroups")
    pointgroup_slug_lookup = attach_pointgroup_slugs(pointgroup_data)
    _log(f"Prepared pointgroup slug lookup ({len(pointgroup_slug_lookup)} symbols)")
    barnighausen = load_barnighausen_data()
    _log(f"Loaded Baernighausen mappings for {len(barnighausen)} source Hall entries")
    euclidian_normalizer_data = load_euclidian_normalizer_data()
    _log(f"Loaded Euclidean normalizer entries for {len(euclidian_normalizer_data)} Hall entries")
    affine_normalizer_data = load_affine_normalizer_data()
    _log(f"Loaded affine normalizer entries for {len(affine_normalizer_data)} Hall entries")
    continuous_euclidian_normalizer_data = load_continuous_euclidian_normalizer_data()
    _log(f"Loaded continuous normalizer entries for {len(continuous_euclidian_normalizer_data)} Hall entries")
    cell_commensurator_data = load_cell_commensurator_data()
    _log(f"Loaded isomorphic subgroup entries for {len(cell_commensurator_data)} Hall entries")
    index_rows = build_index_rows(data)
    _log(f"Built index rows ({len(index_rows)})")
    pointgroup_index_rows = build_pointgroup_index_rows(pointgroup_data)
    _log(f"Built pointgroup index rows ({len(pointgroup_index_rows)})")
    pointgroup_nav = build_pointgroup_nav_rows(pointgroup_data)
    _log(f"Built pointgroup nav rows ({len(pointgroup_nav)})")
    related_settings = build_related_settings(index_rows)
    _log(f"Built related settings map ({len(related_settings)} keys)")
    aliases_by_hall = build_alias_map(symmetry_basics_payload)
    std_setting_transform_data = load_std_setting_transform_data()
    _log(f"Loaded IT-standard setting transforms for {len(std_setting_transform_data)} Hall entries")
    setting_transforms = build_setting_transforms(related_settings, std_setting_transform_data)
    _log(f"Built sibling-setting transform map ({len(setting_transforms)} keys)")
    (
        maximal_subgroup_mappings,
        minimal_supergroup_mappings,
    ) = build_group_mappings(data, barnighausen)
    _log("Built subgroup/supergroup relation maps")

    write_index_content(index_rows)
    write_index_data(index_rows)
    write_pointgroup_index_content()
    write_pointgroup_index_data(pointgroup_index_rows)
    write_pointgroup_pages(pointgroup_data, pointgroup_nav, pointgroup_field_doc_urls)
    write_hall_pages(
        data,
        field_doc_urls,
        aliases_by_hall,
        euclidian_normalizer_data,
        affine_normalizer_data,
        continuous_euclidian_normalizer_data,
        cell_commensurator_data,
        pointgroup_slug_lookup,
        related_settings,
        maximal_subgroup_mappings,
        minimal_supergroup_mappings,
        setting_transforms,
    )
    _log("Generation complete")


if __name__ == "__main__":
    main()
