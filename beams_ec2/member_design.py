"""Adopt one reinforcement cage for all combinations of each physical member."""
import pandas as pd


def design_members(designer, frame, progress_callback=None):
    if frame is None or frame.empty:
        return pd.DataFrame()
    work=frame.copy().reset_index(drop=True)
    work['_input_index']=range(len(work))
    keys=[c for c in ('member','name','story') if c in work]
    rows=[]
    done=0
    for _,group in work.groupby(keys,sort=False,dropna=False):
        # Combining physically different sections into one cage is ambiguous.
        for c in ('material','length','hy','hz','bf','hf','tw','b_top','tf_top','b_bottom','tf_bottom'):
            if c in group and group[c].dropna().nunique()>1:
                raise ValueError(f'{c} varia entre combinações do mesmo membro.')
        floors={'_floor_bot':0.0,'_floor_top':0.0,'_floor_asw':0.0,'_floor_skin':0.0,
                '_force_closed':bool((group.get('t_ed_kNm',pd.Series([0])).abs()>1e-9).any())}
        converged=len(group)==1
        cases='; '.join(group['case'].astype(str))
        for iteration in range(1,9):
            checks=[]
            for _,source in group.iterrows():
                row=source.copy()
                for k,v in floors.items():
                    row[k]=v
                checks.append(designer.design_one(row))
            signatures={(r.get('bot_rebar'),r.get('top_rebar'),r.get('phi_st_mm'),
                         r.get('stirrup_legs'),r.get('s_st_mm'),r.get('skin_rebar')) for r in checks}
            if len(signatures)==1:
                converged=True
                break
            newfloors={**floors,
                '_floor_bot':max(float(r.get('as_prov_bot_mm2',0)) for r in checks),
                '_floor_top':max(float(r.get('as_prov_top_mm2',0)) for r in checks),
                '_floor_asw':max(float(r.get('Asw_s_total_req_mm2_per_m',0))/1000 for r in checks),
                '_floor_skin':max(float(r.get('skin_reinf_face_mm2',0)) for r in checks)}
            floors=newfloors
        for r,(_,source) in zip(checks,group.iterrows()):
            r['adopted_for_cases']=cases
            r['shared_cage_converged']=converged
            r['shared_cage_iterations']=iteration
            r['_input_index']=source['_input_index']
            if not converged:
                r['status']='Falha'
                r['failure_reason']='; '.join(x for x in (r.get('failure_reason',''),'armadura comum às combinações não convergiu') if x)
            rows.append(r)
        done+=len(group)
        if progress_callback:
            progress_callback(done,len(work))
    return pd.DataFrame(rows).sort_values('_input_index').drop(columns='_input_index').reset_index(drop=True)
