"""Select cases without modifying imported rows, positions or calculation methods."""
import re


def select_labels(cases, text, validate_missing=True):
    labels = list(dict.fromkeys(str(case) for case in cases))
    text = str(text or '').strip()
    if not text or text.lower() in {'todas', 'todos', 'all'}:
        from .serviceability import _case_is_els_serviceability
        return {case for case in labels if _case_is_els_serviceability(case)}
    selected = set()
    for block in re.split(r'[;,|]+', text):
        block = block.strip()
        if not block:
            continue
        # Full exported labels remain supported, including spaces in their names.
        if block in labels:
            selected.add(block)
            continue
        if not re.fullmatch(r'\d+(?:\s*[-–]\s*\d+)?(?:\s+\d+(?:\s*[-–]\s*\d+)?)*', block):
            if not validate_missing:
                continue
            raise ValueError('Seleção inválida ou combinação inexistente: ' + block)
        for match in re.finditer(r'(\d+)(?:\s*[-–]\s*(\d+))?', block):
            lo = int(match[1]); hi = int(match[2] or match[1])
            if lo < 1 or hi < lo or hi-lo > 10000:
                raise ValueError('Intervalo de combinações inválido: ' + match[0])
            for number in range(lo, hi+1):
                found = {case for case in labels
                         if re.match(r'^\s*' + str(number) + r'(?!\d)', case)}
                if not found and validate_missing:
                    raise ValueError(f'Combinação não encontrada na tabela: {number}')
                selected.update(found)
    return selected


def select_elu_frame(frame, elu_text='', els_text=''):
    from .serviceability import _case_is_els_serviceability
    cases = frame['case'].astype(str)
    els = select_labels(cases, els_text)
    if str(elu_text or '').strip():
        elu = select_labels(cases, elu_text)
        overlap = elu & els
        if overlap:
            raise ValueError('Combinações em ELU e ELS: ' + ', '.join(sorted(overlap)))
    else:
        elu = {case for case in cases if case not in els and not _case_is_els_serviceability(case)}
    if not elu:
        raise ValueError('Não foram selecionadas combinações ELU para o dimensionamento.')
    selected = frame.loc[cases.isin(elu)].copy()
    if 'limit_state' in selected:
        selected['limit_state'] = 'ELU'
    return selected
