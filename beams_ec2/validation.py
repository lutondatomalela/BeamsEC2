"""Input validation before any envelope can replace invalid values by zero."""
import math
import re


def validate_table(df, moment_axis, shear_axis, torsion_axis):
    if df.empty:
        raise ValueError("Tabela vazia.")
    required = ["member", "case", "length", "hy", "hz", "station",
                moment_axis, shear_axis, torsion_axis]
    missing = [c for c in required if c not in df]
    if missing:
        raise ValueError("Colunas obrigatórias em falta: " + ", ".join(missing))
    numeric = ["length", "hy", "hz", "station", moment_axis, shear_axis, torsion_axis]
    numeric += [c for c in ("fx", "fy", "fz", "mx", "my", "mz") if c in df]
    for c in dict.fromkeys(numeric):
        bad = ~df[c].map(lambda v: isinstance(v, (int, float)) and math.isfinite(v))
        if c == 'station' and 'station_source' in df:
            bad &= ~((df.station_source == 'nó sem posição') & df.station.isna())
        if bad.any():
            rows = [str(i + 2) for i, v in enumerate(bad) if v][:10]
            raise ValueError(f"Valores inválidos em {c}; linhas: {', '.join(rows)}")
    for c in ("length", "hy", "hz"):
        if (df[c] <= 0).any():
            raise ValueError(f"{c} deve ser positivo.")
    if ((df.station < 0) | (df.station > df.length + 1e-8)).any():
        raise ValueError("Estação fora do comprimento do membro.")
    for c in ("member", "case"):
        if df[c].astype(str).str.strip().isin(["", "nan", "None"]).any():
            raise ValueError(f"Identificação {c} em falta.")
    for _, group in df.groupby(["member", "case", "name", "story"], dropna=False):
        for c in ("length", "hy", "hz", "material", "bf", "hf", "tw", "b_top",
                  "tf_top", "b_bottom", "tf_bottom", "section_type_input"):
            if c in group and group[c].dropna().nunique() > 1:
                raise ValueError(f"{c} varia no mesmo membro/caso; dividir o membro em secções constantes.")
    for material in df.material:
        match = re.fullmatch(r"C\s*(\d+)\s*/\s*(\d+)", str(material).strip(), re.I)
        classes = {(12, 15), (16, 20), (20, 25), (25, 30), (30, 37), (35, 45),
                   (40, 50), (45, 55), (50, 60), (55, 67), (60, 75), (70, 85), (80, 95), (90, 105)}
        if not match or tuple(map(int, match.groups())) not in classes:
            raise ValueError(f"Classe de betão não reconhecida: {material}")
