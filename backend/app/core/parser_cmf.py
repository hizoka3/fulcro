"""CMF Informe de Deudas parser (line-based).

pdfplumber's ``extract_text`` lays out each debt row as a single line:

    <institución> <tipo de crédito> DD/MM/YYYY $total $vigente $30-59 $60-89 $90+

We anchor on the date, parse the 5 amounts to its right, and split the
prefix into institución/tipo by matching the rightmost known credit-type
phrase. Header rows and "Total" summary rows are skipped naturally because
they have no date.

Limitations:
- ``num_refinancings`` is detected by keyword count; CMF reports rarely
  include the word, so this signal stays 0 in practice.
- Tipos not in ``_TIPO_PHRASES`` are dropped silently. Add new ones as
  encountered.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pdfplumber

_DATE_RE = re.compile(r"(\d{2}/\d{2}/\d{4})")
_AMOUNT_RE = re.compile(r"\$[\d.\-]+")

# Multi-word tipos go first; standalone words last so they don't shadow longer
# phrases (e.g., "Consumo" inside "Crédito de Consumo" matches the longer one
# via rfind because we prefer the rightmost match).
_TIPO_PHRASES = [
    "Tarjeta de crédito",
    "Tarjeta de Crédito",
    "Tarjeta de Débito",
    "Tarjeta de débito",
    "Línea de Crédito",
    "Linea de Crédito",
    "Línea de crédito",
    "Linea de crédito",
    "Hipoteca con Letra",
    "Hipoteca Endosable",
    "Crédito Hipotecario",
    "Crédito hipotecario",
    "Préstamo Hipotecario",
    "Crédito de Consumo",
    "Crédito Comercial",
    "Crédito Universitario",
    "Operación de Compra",
    "Leasing",
    "Pagaré",
    # Standalone tipos that the CMF report sometimes uses on their own.
    "Comercial",
    "Consumo",
    "Vivienda",
]

# Fragments that appear when pdfplumber wraps a multi-word tipo across two
# lines, e.g. "Tarjeta de" above the data row and "crédito" below it.
_TIPO_FRAGMENT_STARTS = (
    "Tarjeta de",
    "Linea de",
    "Línea de",
    "Hipoteca",
    "Crédito",
    "Préstamo",
)


def parse_informe_cmf(pdf_path: Path) -> Dict:
    features: Dict = {
        "total_debt": 0.0,
        "consumo_debt": 0.0,
        "mortgage_debt": 0.0,
        "commercial_debt": 0.0,
        "past_due_amount": 0.0,
        "consumo_ratio": 0.0,
        "past_due_ratio": 0.0,
        "num_institutions": 0,
        "num_refinancings": 0,
        "has_mortgage": False,
        "carga_financiera_pct": 0.0,
        "dominant_signal": "",
    }
    institutions: set[str] = set()

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

    features["num_refinancings"] = full_text.lower().count("refinanci")

    for row in _extract_debt_rows(full_text):
        institutions.add(row["institucion"])
        tipo_lower = row["tipo"].lower()
        monto = row["total"]
        if monto == 0:
            continue

        if "hipotec" in tipo_lower:
            features["mortgage_debt"] += monto
            features["has_mortgage"] = True
        elif "comercial" in tipo_lower:
            features["commercial_debt"] += monto
        else:
            # Tarjetas, líneas, consumo, leasing, etc. → consumo bucket.
            features["consumo_debt"] += monto

        features["past_due_amount"] += (
            row["atraso_30_59"] + row["atraso_60_89"] + row["atraso_90"]
        )

    features["total_debt"] = (
        features["consumo_debt"] + features["mortgage_debt"] + features["commercial_debt"]
    )
    features["num_institutions"] = len(institutions)

    if features["total_debt"] > 0:
        features["consumo_ratio"] = features["consumo_debt"] / features["total_debt"]
        features["past_due_ratio"] = features["past_due_amount"] / features["total_debt"]

    features["dominant_signal"] = _dominant_signal(features)
    return features


def parse_informe_with_fallback(pdf_path: Path) -> Dict:
    """Wrapper for the demo-mode fallback added in BE1-4. Currently a passthrough."""
    return parse_informe_cmf(pdf_path)


# ---------- internals ----------


def _extract_debt_rows(text: str) -> List[Dict]:
    raw_lines = [line.strip() for line in text.split("\n")]
    rows: List[Dict] = []
    for i, line in enumerate(raw_lines):
        if not line:
            continue
        parsed = _parse_debt_line(line, raw_lines, i)
        if parsed:
            rows.append(parsed)
    return rows


def _parse_debt_line(line: str, all_lines: List[str], idx: int) -> Optional[Dict]:
    date_match = _DATE_RE.search(line)
    if not date_match:
        return None

    before = line[: date_match.start()].strip()
    after = line[date_match.end() :].strip()

    amounts = _AMOUNT_RE.findall(after)
    if len(amounts) < 5:
        return None

    institucion, tipo = _split_institucion_tipo(before)

    # Wrap-around case: tipo split between previous and next lines, e.g.
    #   "Tarjeta de"           ← prev
    #   "<inst> 14/10/2020 ..."  ← current
    #   "crédito"              ← next
    if not tipo:
        prev_line = all_lines[idx - 1] if idx > 0 else ""
        next_line = all_lines[idx + 1] if idx + 1 < len(all_lines) else ""
        if prev_line.startswith(_TIPO_FRAGMENT_STARTS) and next_line:
            combined = f"{prev_line} {next_line}"
            for phrase in _TIPO_PHRASES:
                if phrase.lower() in combined.lower():
                    tipo = phrase
                    institucion = before
                    break

    if not institucion or not tipo:
        return None

    return {
        "institucion": institucion,
        "tipo": tipo,
        "fecha": date_match.group(1),
        "total": _parse_clp(amounts[0]),
        "vigente": _parse_clp(amounts[1]),
        "atraso_30_59": _parse_clp(amounts[2]),
        "atraso_60_89": _parse_clp(amounts[3]),
        "atraso_90": _parse_clp(amounts[4]),
    }


def _split_institucion_tipo(prefix: str) -> Tuple[Optional[str], Optional[str]]:
    """Find the rightmost known tipo phrase in `prefix`."""
    best_idx = -1
    best_phrase: Optional[str] = None
    for phrase in _TIPO_PHRASES:
        idx = prefix.rfind(phrase)
        if idx > best_idx:
            best_idx = idx
            best_phrase = phrase
    if best_idx < 0 or best_phrase is None:
        return None, None
    institucion = prefix[:best_idx].strip()
    tipo = prefix[best_idx : best_idx + len(best_phrase)].strip()
    return institucion or None, tipo or None


def _parse_clp(s) -> float:
    if not s:
        return 0.0
    cleaned = str(s).replace("$", "").replace(".", "").replace(" ", "").strip()
    if not cleaned or cleaned == "-":
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _dominant_signal(features: Dict) -> str:
    if features["past_due_ratio"] > 0:
        return "past_due_present"
    if features["consumo_ratio"] > 0.7:
        return "high_consumo_ratio"
    if features["num_refinancings"] >= 2:
        return "multiple_refinancings"
    if features["num_institutions"] >= 4:
        return "many_institutions"
    if features["has_mortgage"]:
        return "stable_with_mortgage"
    return "low_engagement"
