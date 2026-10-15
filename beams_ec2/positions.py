"""Read dimensional Robot point labels without assigning positions to node IDs."""
import pandas as pd


def extract_positions(frame):
    if 'station' in frame:
        frame['station_source'] = 'coluna'
        return frame
    labels = frame['node'].astype(str).str.strip()
    numbers = labels.str.extract(
        r'(?i)\bx\s*=\s*([+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?)',
        expand=False)
    frame['station'] = pd.to_numeric(numbers.str.replace(',', '.', regex=False), errors='coerce')
    frame['station_source'] = 'ponto x (m)'
    start = labels.str.match(r'(?i)^(?:start|origin)\s*\(\s*\d+\s*\)$')
    end = labels.str.match(r'(?i)^end\s*\(\s*\d+\s*\)$')
    frame.loc[start, 'station'] = 0.0
    frame.loc[end, 'station'] = frame.loc[end, 'length']
    frame.loc[start | end, 'station_source'] = 'extremo explícito'
    unknown = labels.str.fullmatch(r'\d+')
    frame.loc[unknown, 'station_source'] = 'nó sem posição'
    return frame
