"""Readable, paginatable engineering tables for the report exporters."""
from functools import lru_cache
from html import escape
import math
import os
from pathlib import Path
import pandas as pd


@lru_cache(maxsize=1)
def ensure_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    roots=[(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts','cour.ttf','courbd.ttf'),
           (Path('/usr/share/fonts/truetype/msttcorefonts'),'cour.ttf','courbd.ttf'),
           (Path('/usr/share/fonts/truetype/dejavu'),'DejaVuSansMono.ttf','DejaVuSansMono-Bold.ttf')]
    for root,normal,bold in roots:
        if (root/normal).is_file() and (root/bold).is_file():
            pdfmetrics.registerFont(TTFont('Courier',str(root/normal)))
            pdfmetrics.registerFont(TTFont('Courier-Bold',str(root/bold)))
            pdfmetrics.registerFontFamily('Courier',normal='Courier',bold='Courier-Bold',
                                         italic='Courier',boldItalic='Courier-Bold')
            return str(root/normal)
    return 'Courier (standard PDF font)'


LABELS={
 'combination_group':'Grupo de combinação','limit_state':'Estado limite',
 'service_count_ELS_CAR':'ELS características','service_count_ELS_FREQ':'ELS frequentes',
 'service_count_ELS_QP':'ELS quase-permanentes','service_creep_status':'Validade da fluência linear',
 'viga':'Viga','member':'Membro','case':'Combinação','story':'Piso',
 'section_type':'Secção','section_geometry_summary':'Geometria [cm]',
 'section_geometry_source':'Origem da geometria','section_geometry_confidence':'Confiança',
 'section_fit_error_pct':'Erro geométrico [%]','n_points_found':'Estações',
 'length':'L [m]','material':'Betão','m_pos_ed_kNm':'M+Ed [kNm]',
 'm_neg_ed_kNm':'M-Ed [kNm]','mrd_pos_kNm':'M+Rd [kNm]','mrd_neg_kNm':'M-Rd [kNm]',
 'eta_m_pos':'η M+','eta_m_neg':'η M-','eta_vt':'η corte/torção',
 'v_ed_kN':'VEd [kN]','VRd_c_kN':'VRd,c [kN]','VRd_max_kN':'VRd,max [kN]',
 't_ed_kNm':'TEd [kNm]','TRd_max_kNm':'TRd,max [kNm]',
 'cot_theta_shear':'cot θ (corte)','cot_theta_torsion':'cot θ (torção)',
 'bot_rebar':'Armadura inferior','top_rebar':'Armadura superior','skin_rebar':'Armadura lateral',
 'phi_st_mm':'Ø estribo [mm]','stirrup_legs':'Ramos','s_st_mm':'s estribos [mm]',
 'Asw_s_total_req_mm2_per_m':'Asw/s necessária [mm²/m]',
 'Asw_s_prov_mm2_per_m':'Asw/s adotada [mm²/m]',
 'bot_clear_spacing_mm':'Livre inferior [mm]','top_clear_spacing_mm':'Livre superior [mm]',
 'ductility_pos':'Flexão positiva','ductility_neg':'Flexão negativa',
 'torsion_considered':'Torção considerada','torsion_status':'Verificação da torção',
 'shear_status':'Verificação do corte','stirrup_status':'Verificação dos estribos',
 'status':'Estado','solution':'Solução adotada','failure_reason':'Motivo / nota',
 'failure_type':'Tipo de falha','detailing_status':'Pormenorização','detailing_issues':'Notas de pormenorização',
 'service_combinations_checked':'Combinações ELS',
 'service_combination_crack':'ELS governante wk','service_combination_deflection':'ELS governante flecha',
 'service_combination_steel':'ELS governante aço','service_combination_concrete':'ELS governante betão',
 'service_support_condition':'Condição de apoio','service_history_mode':'Histórico',
 'service_reinforcement_model':'Armadura usada em ELS',
 'service_wk_est_mm':'wk [mm]','service_wk_lim_mm':'wk,lim [mm]',
 'service_deflection_est_mm':'Flecha [mm]','service_deflection_lim_mm':'Flecha limite [mm]',
 'service_sigma_s_MPa':'σs [MPa]','service_sigma_c_MPa':'σc [MPa]',
 'service_status':'Estado ELS','lbd_bot_mm':'lbd inferior [mm]','lbd_top_mm':'lbd superior [mm]',
 'shift_al_mm':'Decalagem al [mm]','extension_bot_mm':'Extensão inferior [mm]',
 'extension_top_mm':'Extensão superior [mm]','min_bottom_bars_into_support':'Varões no apoio',
 'detailing_note':'Nota de pormenorização','shared_cage_converged':'Armadura comum verificada',
 'adopted_for_cases':'Combinações abrangidas',
}


def cell_text(value,column):
    if column=='combination_group':
        return {'ELU':'ELU','ELS_CAR':'ELS característica','ELS_FREQ':'ELS frequente','ELS_QP':'ELS quase-permanente','NAO_CLASSIFICADA':'Não classificada / excluída'}.get(str(value),str(value))
    if value is None or (not isinstance(value,(list,dict)) and pd.isna(value)):
        return '-'
    if isinstance(value,bool):
        return 'Sim' if value else 'Não'
    if isinstance(value,(float,int)):
        if not math.isfinite(float(value)):
            return '-'
        if column in {'n_points_found','stirrup_legs','service_combinations_checked','service_points_imported','service_points_integrated'} or column.endswith(('_iterations','_layers')):
            return str(int(value))
        digits=3 if ('wk' in column or column.startswith('eta_')) else 2
        return f'{value:.{digits}f}'
    return str(value)


def engineering_table(app,frame,columns,max_rows,widths,styles):
    from reportlab.lib.units import mm
    from reportlab.platypus import Table,Paragraph,Spacer,Flowable
    from reportlab.platypus.doctemplate import NullActionFlowable
    class TableSequence(Flowable):
        def __init__(self,parts):
            super().__init__()
            self.parts=parts
            self._engineering_tables=parts
        def wrap(self,available_width,available_height):
            return 0,1e12
        def split(self,available_width,available_height):
            # Expand into the story without forcing the whole group onto
            # the next page. Individual tables retain normal pagination.
            return [NullActionFlowable()]+self.parts
    from reportlab.lib.styles import ParagraphStyle
    if frame is None or frame.empty:
        return Paragraph('Sem dados.',styles['Small'])
    cols=[c for c in columns if c in frame]
    if not cols:
        return Paragraph('Sem colunas aplicáveis.',styles['Small'])
    selected=frame if max_rows is None else frame.head(max_rows)
    ids=[c for c in ('viga','Viga','member','case','Caso') if c in cols][:2]
    if 'Etapa' in cols and 'Item' in cols:
        ids+=['Etapa','Item']
    if len(cols)>8:
        rest=[c for c in cols if c not in ids]
        groups=[ids+rest[i:i+8-len(ids)] for i in range(0,len(rest),8-len(ids))]
    else:
        groups=[cols]
    header=ParagraphStyle('EngineeringHeader',parent=styles['Cell'],fontName='Courier-Bold')
    parts=[]
    for group in groups:
        data=[[Paragraph(escape(LABELS.get(c,c.replace('_',' '))),header) for c in group]]
        for _,row in selected.iterrows():
            data.append([Paragraph(escape(cell_text(row.get(c),c)),styles['Cell']) for c in group])
        sizes=[v*mm for v in widths] if len(groups)==1 and widths and len(widths)==len(group) else [270*mm/len(group)]*len(group)
        table=Table(data,colWidths=sizes,repeatRows=1,hAlign='LEFT')
        table.setStyle(app._pdf_table_style(header=True))
        parts.extend([table,Spacer(1,3*mm)])
    return parts[0] if len(groups)==1 else TableSequence(parts)


def flatten_tables(story):
    from reportlab.platypus import CondPageBreak
    result=[]
    for item in story:
        if getattr(getattr(item,'style',None),'name','') in {'BodyCourier','Section'}:
            # Reserve space for a heading and the first table rows, without
            # keeping an entire multi-page table on the following page.
            result.append(CondPageBreak(80))
        result.extend(getattr(item,'_engineering_tables',[item]))
    return result
