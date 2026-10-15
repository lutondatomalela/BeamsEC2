"""Explicit, disjoint limit-state groups; unselected cases never become ULS."""
import re
import unicodedata
from dataclasses import replace

GROUPS=('ELU','ELS_CAR','ELS_FREQ','ELS_QP')
VARIABLES={'ELU':'var_elu_cases','ELS_CAR':'var_sls_char_cases',
           'ELS_FREQ':'var_sls_freq_cases','ELS_QP':'var_sls_qp_cases'}
REGIMES={'ELS_CAR':'Característica / curta duração',
         'ELS_FREQ':'Frequente / repetida','ELS_QP':'Quase-permanente / longo prazo'}


def parse_cases(text):
    text=str(text or '').strip().replace('–','-').replace('—','-').replace('‑','-').replace('−','-').replace('‐','-')
    text=re.sub(r'(\d)\s*-\s*(\d)',r'\1-\2',text)
    result=set()
    for token in re.split(r'[\s,;|]+',text):
        if not token:continue
        if not re.fullmatch(r'\d+(?:-\d+)?',token):
            raise ValueError(f'Identificador de combinação inválido: {token}')
        bounds=list(map(int,token.split('-')))
        start,end=(bounds[0],bounds[-1])
        if start<1 or end<start or end-start>10000:
            raise ValueError(f'Intervalo de combinações inválido: {token}')
        result.update(range(start,end+1))
    return result


def case_number(case):
    found=re.search(r'\b(\d+)\b',str(case).replace('_',' '))
    return int(found.group(1)) if found else None


def named_group(case):
    name=unicodedata.normalize('NFKD',str(case)).encode('ascii','ignore').decode().upper().replace('_',' ')
    def contains(pattern):return re.search(pattern,name) is not None
    # '(C)' merely means combination; conflicting explicit names are unsafe.
    hints=[]
    if contains(r'\b(ELU|ULS)\b'):hints.append('ELU')
    if contains(r'\b(QP|CQC)\b|QUASE|QUASI|Q\.P\.'):hints.append('ELS_QP')
    if contains(r'FREQ|REPET'):hints.append('ELS_FREQ')
    if contains(r'CARACT|CHARACTER|\bCHAR\b|\bCAR\b|\bRARA\b'):hints.append('ELS_CAR')
    return hints[0] if len(hints)==1 else 'NAO_CLASSIFICADA'


def selections_from_app(app):
    return {group:str(getattr(app,name).get()).strip() if hasattr(app,name) else ''
            for group,name in VARIABLES.items()}


def classify_combinations(frame,selections,validate_missing=True):
    groups={key:parse_cases(selections.get(key,'')) for key in GROUPS}
    assigned={}
    for group,numbers in groups.items():
        for number in numbers:
            if number in assigned:
                raise ValueError(f'Combinação {number} atribuída a {assigned[number]} e {group}.')
            assigned[number]=group
    cases=list(frame.case.drop_duplicates())
    available={case_number(c) for c in cases}
    missing=set(assigned)-available
    if missing and validate_missing:
        raise ValueError('Combinações não encontradas na tabela: '+', '.join(map(str,sorted(missing))))
    manual=any(groups.values())
    out=frame.copy()
    mapping={c:assigned.get(case_number(c),'NAO_CLASSIFICADA') if manual else named_group(c) for c in cases}
    out['combination_group']=out.case.map(mapping)
    out['limit_state']=out.combination_group.map(lambda g:'ELU' if g=='ELU' else 'ELS' if g.startswith('ELS_') else 'Não classificada')
    out['combination_classification_source']='seleção do utilizador' if manual else 'nome explícito da combinação'
    return out


def parameters_for_group(base,group):
    return replace(base,regime=REGIMES[group],auto_regime=False)


def apply_check_policy(result,group):
    out=result.copy();out['service_group']=group
    if result.get('service_status')=='Dados insuficientes':return out
    raw={k:out.get(k) for k in ('service_crack_status','service_deflection_status','service_stress_status','service_concrete_status')}
    for key in raw:out[key]='Informativo'
    if group=='ELS_CAR':
        active=('service_stress_status','service_concrete_status')
    elif group=='ELS_QP':
        active=('service_crack_status','service_deflection_status')
        out['service_creep_status']='OK' if raw['service_concrete_status']=='OK' else 'Requer fluência não linear'
    else:
        active=()
    for key in active:out[key]=raw[key]
    out['service_status']='Não verifica' if any(out[k]=='Não verifica' for k in active) else 'OK'
    if group=='ELS_QP' and out.get('service_creep_status')!='OK' and out['service_status']=='OK':
        out['service_status']='Dados insuficientes'
        out['service_note']=out.get('service_note','')+' Tensão QP superior a 0,45 fck: requer fluência não linear.'
    if group=='ELS_FREQ':
        out['service_status']='Informativo'
        out['service_note']=out.get('service_note','')+' Regime frequente informativo; não substitui CAR ou QP.'
    return out
