# -*- coding: utf-8 -*-
"""Leitura robusta de tabelas de entrada.

Suporta livros de cálculo modernos e legados, bem como tabelas de texto com
codificações e separadores usuais. O tipo real do ficheiro é detectado pela
assinatura binária, sem depender apenas da extensão.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import io
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class TableReadInfo:
    format_name: str
    encoding: str = ""
    separator: str = ""

    @property
    def description(self) -> str:
        parts = [self.format_name]
        if self.encoding:
            parts.append(self.encoding)
        if self.separator:
            label = {"\t": "tabulação", ";": "ponto e vírgula", ",": "vírgula", "|": "barra vertical"}.get(self.separator, self.separator)
            parts.append(f"separador: {label}")
        return "; ".join(parts)


_ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
_OLE_SIGNATURE = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"


def _decode_text(data: bytes) -> tuple[str, str]:
    if not data:
        return "", "utf-8"

    preferred: list[str] = []
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        preferred.append("utf-16")
    elif data.startswith(b"\xef\xbb\xbf"):
        preferred.append("utf-8-sig")

    preferred.extend(["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "cp1252", "latin-1"])
    tried: set[str] = set()
    for encoding in preferred:
        if encoding in tried:
            continue
        tried.add(encoding)
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        # Uma descodificação UTF-16 incorrecta costuma produzir muitos NUL.
        if text and text.count("\x00") > max(2, len(text) // 100):
            continue
        return text.lstrip("\ufeff"), encoding
    raise UnicodeError("não foi possível reconhecer a codificação da tabela")


def _candidate_separators(header: str) -> Iterable[str]:
    ordered = ["\t", ";", "|", ","]
    present = [sep for sep in ordered if sep in header]
    if present:
        return present + [sep for sep in ordered if sep not in present]
    return ordered


def _read_delimited_text(text: str) -> tuple[pd.DataFrame, str]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return pd.DataFrame(), ""

    header = lines[0]
    candidates: list[tuple[float, str, pd.DataFrame]] = []
    for sep in _candidate_separators(header):
        try:
            frame = pd.read_csv(
                io.StringIO(text),
                sep=sep,
                engine="python",
                dtype=str,
                keep_default_na=False,
                na_filter=False,
            )
        except Exception:
            continue
        ncols = len(frame.columns)
        if ncols <= 1:
            continue
        unnamed = sum(str(c).strip().lower().startswith("unnamed") for c in frame.columns)
        empty_headers = sum(not str(c).strip() for c in frame.columns)
        # Favorece cabeçalhos consistentes e penaliza separações espúrias.
        score = ncols * 10.0 - unnamed * 4.0 - empty_headers * 4.0
        if sep == "\t" and "\t" in header:
            score += 5.0
        if sep == ";" and ";" in header:
            score += 4.0
        candidates.append((score, sep, frame))

    if candidates:
        _, sep, frame = max(candidates, key=lambda item: item[0])
        frame.columns = [str(c).strip().lstrip("\ufeff") for c in frame.columns]
        return frame, sep

    # Último recurso: Sniffer para tabelas menos usuais.
    try:
        dialect = csv.Sniffer().sniff("\n".join(lines[:20]), delimiters="\t;,|")
        frame = pd.read_csv(io.StringIO(text), sep=dialect.delimiter, engine="python", dtype=str, keep_default_na=False, na_filter=False)
        frame.columns = [str(c).strip().lstrip("\ufeff") for c in frame.columns]
        return frame, dialect.delimiter
    except Exception as exc:
        raise ValueError("a tabela de texto não contém um separador reconhecível") from exc


def read_table_file(path: str | Path) -> tuple[pd.DataFrame, TableReadInfo]:
    """Lê uma tabela e devolve os dados e a descrição do formato detectado."""
    file_path = Path(path)
    data = file_path.read_bytes()

    # Livros modernos: ZIP/OOXML.
    if data.startswith(_ZIP_SIGNATURES):
        frame = pd.read_excel(file_path, dtype=str, keep_default_na=False)
        return frame, TableReadInfo("livro de cálculo (.xlsx)")

    # Livros legados OLE. A dependência xlrd é declarada no requirements.txt.
    if data.startswith(_OLE_SIGNATURE):
        frame = pd.read_excel(file_path, dtype=str, keep_default_na=False)
        return frame, TableReadInfo("livro de cálculo legado (.xls)")

    # Alguns programas guardam tabelas delimitadas com extensão .xls/.xlsx.
    text, encoding = _decode_text(data)
    frame, separator = _read_delimited_text(text)
    return frame, TableReadInfo("tabela de texto", encoding=encoding, separator=separator)
