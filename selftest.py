# -*- coding: utf-8 -*-
"""Testes de sanidade e regressão da versão pública."""

from pathlib import Path
import tempfile

import pandas as pd

from beams_ec2.advanced import _internal_tests_advanced
from beams_ec2.release import _prepare_input_frames, read_table_file


def _i_section_sample() -> pd.DataFrame:
    return pd.DataFrame([{
        "Member/Node/Case": "87/169/101 (C)",
        "Station (m)": "0",
        "FX (kN)": "42,14",
        "FY (kN)": "0,00",
        "FZ (kN)": "127,62",
        "MX (kNm)": "0,00",
        "MY (kNm)": "0,00",
        "MZ (kNm)": "0,00",
        "Length (m)": "18,80",
        "Material": "C50/60",
        "HY (cm)": "40,0",
        "HZ (cm)": "70,0",
        "VY (cm)": "20,0",
        "VZ (cm)": "35,5",
        "VPY (cm)": "20,0",
        "VPZ (cm)": "34,5",
        "AX (cm2)": "1350,29",
        "AY (cm2)": "800,40",
        "AZ (cm2)": "549,89",
        "IX (cm4)": "41734,21",
        "IY (cm4)": "840694,63",
        "IZ (cm4)": "112264,72",
    }])


def _public_regression_tests() -> pd.DataFrame:
    rows = []
    sample = _i_section_sample()

    clean, envelopes = _prepare_input_frames(sample)
    detected = str(envelopes.iloc[0].get("section_type", "")) if not envelopes.empty else ""
    rows.append({
        "Teste": "Identificação de secção I assimétrica",
        "Calculado": detected,
        "Referência": "I assimétrica",
        "Unidade": "-",
        "Erro relativo": 0.0 if detected == "I assimétrica" else 1.0,
        "Tolerância": 0.0,
        "Estado": "OK" if detected == "I assimétrica" else "Falha",
    })

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        text = "\t".join(sample.columns) + "\n" + "\t".join(str(value) for value in sample.iloc[0].tolist()) + "\n"
        legacy_named = temp / "tabela_utf16.xls"
        legacy_named.write_bytes(text.encode("utf-16"))
        imported, info = read_table_file(legacy_named)
        clean_utf16, env_utf16 = _prepare_input_frames(imported)
        detected_utf16 = str(env_utf16.iloc[0].get("section_type", "")) if not env_utf16.empty else ""
        import_ok = len(imported) == 1 and detected_utf16 == "I assimétrica" and info.encoding == "utf-16"
        rows.append({
            "Teste": "Importação UTF-16 com separador tabulado",
            "Calculado": f"{len(imported)} linha; {detected_utf16}",
            "Referência": "1 linha; I assimétrica",
            "Unidade": "-",
            "Erro relativo": 0.0 if import_ok else 1.0,
            "Tolerância": 0.0,
            "Estado": "OK" if import_ok else "Falha",
        })

    required_geometry = {"ax", "iy", "iz", "vz_sec", "vpz_sec"}
    geometry_ok = required_geometry.issubset(set(clean.columns))
    rows.append({
        "Teste": "Preservação das propriedades geométricas",
        "Calculado": ", ".join(sorted(required_geometry.intersection(clean.columns))),
        "Referência": ", ".join(sorted(required_geometry)),
        "Unidade": "-",
        "Erro relativo": 0.0 if geometry_ok else 1.0,
        "Tolerância": 0.0,
        "Estado": "OK" if geometry_ok else "Falha",
    })

    return pd.DataFrame(rows)


def main():
    results = pd.concat([_internal_tests_advanced(), _public_regression_tests()], ignore_index=True)
    print(results.to_string(index=False))
    failed = results[results["Estado"] != "OK"]
    raise SystemExit(1 if not failed.empty else 0)


if __name__ == "__main__":
    main()
