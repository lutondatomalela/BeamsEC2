"""Explicit service groups and governing checks; independent of table positions."""
from dataclasses import replace
import math
from .case_selection import select_labels

FIELDS = {'ELU':'var_elu_cases', 'ELS_CAR':'var_sls_char_cases',
          'ELS_FREQ':'var_sls_freq_cases', 'ELS_QP':'var_sls_qp_cases'}
REGIMES = {'ELS_CAR':'Característica / curta duração',
           'ELS_FREQ':'Frequente / repetida', 'ELS_QP':'Quase-permanente / longo prazo'}


def selections(app):
    return {g:str(getattr(app,n).get()).strip() if hasattr(app,n) else '' for g,n in FIELDS.items()}


def resolve(cases, texts):
    """None keeps legacy mode. In explicit mode, every unassigned case is excluded."""
    if not any(texts.get(g,'').strip() for g in REGIMES):
        return None
    assigned = {}
    for group in FIELDS:
        text = texts.get(group,'').strip()
        if not text:
            continue
        if text.lower() in {'all','todos','todas'}:
            raise ValueError('Nos grupos explícitos, indique números ou nomes das combinações.')
        for case in select_labels(cases,text):
            if case in assigned:
                raise ValueError(f'Combinação {case} atribuída a {assigned[case]} e {group}.')
            assigned[case]=group
    return {str(case):assigned.get(str(case),'EXCLUIDA') for case in cases}


def parameters(base, group):
    return replace(base, regime=REGIMES[group], auto_regime=False)


def policy(raw, group):
    out=raw.copy(); out['service_group']=group
    if group == 'ELS_FREQ':
        for key in ('crack','deflection','stress','concrete'):
            out['service_'+key+'_status']='Informativo'
        out['service_status']='Informativo'
        return out
    active=('stress','concrete') if group=='ELS_CAR' else ('crack','deflection')
    for name in ('crack','deflection','stress','concrete'):
        key='service_'+name+'_status'
        out[key]=raw.get(key,'Dados insuficientes') if name in active else 'Informativo'
    if group=='ELS_QP':
        c=raw.get('service_concrete_status')
        out['service_creep_status']=('OK' if c=='OK' else 'Requer fluência não linear'
                                     if c=='Não verifica' else 'Dados insuficientes')
        inferred = any(word in str(raw.get('service_diagram_source',''))
                       for word in ('ordem das linhas', 'ajustadas', 'normalizadas'))
        if inferred or raw.get('service_diagram_quality')=='Insuficiente' or raw.get('service_status')=='Dados insuficientes':
            out['service_deflection_status']='Dados insuficientes'
    if raw.get('service_axial_ratio',0)>0.10:
        for name in active:
            out['service_'+name+'_status']='Dados insuficientes'
        if group=='ELS_QP':out['service_creep_status']='Dados insuficientes'
    statuses=[out['service_'+n+'_status'] for n in active]
    if group=='ELS_QP':statuses.append(out['service_creep_status'])
    out['service_status']=('Não verifica' if 'Não verifica' in statuses else
                           'OK' if all(v=='OK' for v in statuses) else 'Dados insuficientes')
    return out


def envelope(items):
    # Keep the QP model metadata; each governing check below replaces its own values.
    seed = next((d for d in items if d.get('service_group')=='ELS_QP'), items[0] if items else {})
    result = seed.copy()
    specs=[('crack','ELS_QP','service_wk_est_mm','service_wk_lim_mm',
            ['service_wk_est_mm','service_wk_lim_mm','service_crack_status']),
           ('deflection','ELS_QP','service_deflection_est_mm','service_deflection_lim_mm',
            ['service_deflection_instant_mm','service_deflection_final_mm','service_deflection_est_mm',
             'service_deflection_lim_mm','service_deflection_limit','service_deflection_status']),
           ('steel','ELS_CAR','service_sigma_s_MPa','service_sigma_s_lim_MPa',
            ['service_sigma_s_MPa','service_sigma_s_lim_MPa','service_stress_status']),
           ('concrete','ELS_CAR','service_sigma_c_MPa','service_sigma_c_lim_MPa',
            ['service_sigma_c_MPa','service_sigma_c_lim_MPa','service_concrete_status']),
           ('creep','ELS_QP','service_sigma_c_MPa','service_sigma_c_lim_MPa',['service_creep_status'])]
    missing=[]
    for name,group,value,limit,keys in specs:
        candidates=[d for d in items if d.get('service_group')==group and
                    isinstance(d.get(value),(float,int)) and math.isfinite(d[value])]
        chosen=max(candidates,key=lambda d:d[value]/max(d.get(limit,0),1e-12)) if candidates else {}
        result['service_combination_'+name]=chosen.get('service_combination','')
        result['service_group_'+name]=group
        for key in keys:
            result[key]=chosen.get(key,'Dados insuficientes' if key.endswith('status') else float('nan'))
        if name=='creep':
            result['service_creep_sigma_c_MPa']=chosen.get(value,float('nan'))
            result['service_creep_sigma_c_lim_MPa']=chosen.get(limit,float('nan'))
        if not chosen:missing.append(group)
    # A failed or incomplete non-governing case must not disappear from the audit.
    active=[d for d in items if d.get('service_group') in ('ELS_CAR','ELS_QP')]
    result['service_status']=('Não verifica' if any(d.get('service_status')=='Não verifica' for d in active)
                              else 'Dados insuficientes' if missing or any(d.get('service_status')!='OK' for d in active)
                              else 'OK')
    result['service_combinations_checked']=len(items)
    result['service_combinations_list']='; '.join(str(d.get('service_combination','')) for d in items)
    result['service_governing_combination']=result.get('service_combination_deflection','')
    result['service_note']='Grupos explícitos: tensões CAR; fissuração e flecha QP; frequentes informativos.'
    if missing:result['service_note']+=' Grupos em falta ou sem resultados: '+', '.join(sorted(set(missing)))+'.'
    if result['service_creep_status']=='Requer fluência não linear':
        result['service_note']+=' Tensão QP superior ao limite de fluência linear; rever modelo de fluência.'
    pending, required = incomplete_diagnostics(items, missing)
    result['service_pending_checks'] = pending
    result['service_required_data'] = required
    if pending:
        result['service_note'] += ' Por concluir: ' + pending + '. ' + required
    return result


def incomplete_diagnostics(items, missing):
    """Explain incomplete checks without changing their engineering status."""
    pending = []
    actions = []
    for group in sorted(set(missing)):
        pending.append('Regime ' + group)
        actions.append('Indicar combinações ' + group + ' com resultados importados para esta viga.')
    names = {'stress':'Tensão no aço', 'concrete':'Tensão no betão', 'crack':'Fendilhação', 'deflection':'Flecha', 'creep':'Fluência linear'}
    for item in items:
        group = item.get('service_group')
        checks = ('stress','concrete') if group=='ELS_CAR' else ('crack','deflection','creep') if group=='ELS_QP' else ()
        for check in checks:
            if check == 'creep' and item.get('service_creep_status') == 'Requer fluência não linear':
                pending.append('Modelo de fluência [' + str(item.get('service_combination', '')) + ']')
                actions.append('Verificar com um modelo de fluência não linear adequado à tensão de compressão quase-permanente.')
                continue
            if item.get('service_'+check+'_status') != 'Dados insuficientes':
                continue
            case = str(item.get('service_combination',''))
            pending.append(names[check] + ' [' + case + ']')
            if item.get('service_axial_ratio',0) > .10:
                actions.append('Verificar ELS com um modelo que considere o esforço normal relevante; acrescentar estações não resolve esta limitação.')
            elif check == 'deflection':
                source = str(item.get('service_diagram_source',''))
                actions.append('Fornecer Station (m) com posições físicas, cobrindo o vão e os apoios, e pelo menos três posições distintas (preferencialmente cinco ou mais); confirmar comprimento e condição de apoio.' + (' Origem atual: '+source+'.' if source else ''))
            else:
                actions.append('Confirmar esforços, secção, materiais e armadura da combinação '+case+'; consultar a nota de cálculo por combinação.')
    return '; '.join(dict.fromkeys(pending)), ' '.join(dict.fromkeys(actions))
