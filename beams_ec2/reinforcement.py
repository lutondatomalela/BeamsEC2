"""Bounded iteration of real reinforcement positions and section resistance.

The solver keeps the design instance immutable. Each stirrup diameter is solved
independently; no effective depth is reused from a different cage.
"""

def mean_tension_width(section):
    """EC2 9.2.1.1: mean tension-zone width; compressed T flange excluded."""
    if section.is_t and section.top_thickness_mm>0 and section.bottom_thickness_mm==0:
        return section.web_mm
    _,centroid,_,_=section.gross_properties()
    area=sum(max(0.0,z1-max(z0,centroid))*b for z0,z1,b in section.segments)
    return area/(section.h_mm-centroid)


def solve_reinforcement(designer, section, cp, fyd, mpos, mneg, ved, tors,
                        choose_face, extra_bot=0.0, extra_top=0.0, floors=None):
    h, bw = section.h_mm, section.web_mm
    floors = {} if floors is None else floors
    active = tors.get('torsion_considered') == 'Sim' or bool(floors.get('_force_closed',False))
    alternatives = []
    for phi_st in (8.0, 10.0, 6.0):
        depth = h - designer.cover_mm - phi_st - 8.0
        edge = designer.cover_mm + phi_st + 8.0
        if not 0 < edge < depth:
            continue
        target_bot = float(floors.get('_floor_bot',0))
        target_top = float(floors.get('_floor_top',0))
        last = None
        for iteration in range(1, 25):
            db, dt, d2b, d2t = (depth, depth, edge, edge) if last is None else (
                last['d_bot'], last['d_top'], last['d2_bot'], last['d2_top'])
            fpos = designer.flexural_required(mpos, section, db, d2t, cp['fcd'], fyd)
            fneg = designer.flexural_required(mneg, section.flipped(), dt, d2b, cp['fcd'], fyd)
            min_bot = designer.as_min_beam(mean_tension_width(section), db, cp['fctm'], designer.fyk)
            min_top = designer.as_min_beam(mean_tension_width(section.flipped()), dt, cp['fctm'], designer.fyk)
            target_bot = max(target_bot, min_bot,
                             max(fpos['As_req'], fneg.get('As_comp_req', 0)) + extra_bot)
            target_top = max(target_top, min_top,
                             max(fneg['As_req'], fpos.get('As_comp_req', 0)) + extra_top)
            bot = choose_face(designer, target_bot, section, 'bottom', phi_st, perimeter=active)
            top = choose_face(designer, target_top, section, 'top', phi_st, perimeter=active)
            db = h - bot.centroid_from_edge_mm if bot.n_bars else depth
            dt = h - top.centroid_from_edge_mm if top.n_bars else depth
            d2b = bot.centroid_from_edge_mm if bot.n_bars else edge
            d2t = top.centroid_from_edge_mm if top.n_bars else edge
            positions_valid = 0 < d2t < db <= h and 0 < d2b < dt <= h
            gap = h - (max(getattr(bot,'layer_depths_mm',[d2b]))+bot.phi_mm/2) - (max(getattr(top,'layer_depths_mm',[d2t]))+top.phi_mm/2)
            layout_valid = gap >= designer.min_clear_spacing(max(bot.phi_mm,top.phi_mm))-1e-9
            layout_valid &= max(bot.area_mm2,top.area_mm2) <= 0.04*section.gross_properties()[0]+1e-8
            zero = {'MRd_kNm': 0.0, 'x_mm': None, 'z_mm': None}
            mrp = designer.flexural_capacity(max(0,bot.area_mm2-extra_bot), max(0,top.area_mm2-extra_top), section, db, d2t, cp['fcd'], fyd) if positions_valid else zero
            mrn = designer.flexural_capacity(max(0,top.area_mm2-extra_top), max(0,bot.area_mm2-extra_bot), section.flipped(), dt, d2b, cp['fcd'], fyd) if positions_valid else zero
            shear = designer.shear_requirements(ved, bw, min(db, dt), min(bot.area_mm2, top.area_mm2), cp['fck'], cp['fcd'], fyd)
            asw = max(shear['Asw_s_min_mm2_per_mm'], shear['Asw_s_shear_req_mm2_per_mm']) + (tors.get('Asw_s_torsion_req_mm2_per_mm') or 0.0)
            asw=max(asw,float(floors.get('_floor_asw',0)))
            stir = designer.choose_stirrups(asw, bw, h, min(db, dt), active, phi_st_mm=phi_st)
            cap_ok = mrp['MRd_kNm'] + 1e-7 >= mpos and mrn['MRd_kNm'] + 1e-7 >= mneg
            # Repeat at the adopted positions before accepting any design.
            stable = last is not None and (bot.label, top.label, bot.layers, top.layers) == last['signature']
            last = dict(bot=bot, top=top, d_bot=db, d_top=dt, d2_bot=d2b, d2_top=d2t,
                        Mrd_pos=mrp, Mrd_neg=mrn, shear=shear, stir=stir, Asw_total=asw,
                        As_min_bot=min_bot, As_min_top=min_top, As_req_bot=target_bot,
                        As_req_top=target_top, flex_pos=fpos, flex_neg=fneg,
                        signature=(bot.label, top.label, bot.layers, top.layers),
                        reinforcement_iterations=iteration, reinforcement_converged=False,
                        reinforcement_stirrup_assumed_mm=phi_st)
            if bot.status != 'OK' or top.status != 'OK' or not positions_valid:
                break
            if stable and cap_ok:
                last['reinforcement_converged'] = layout_valid
                break
            if not cap_ok:
                # Advance to a larger discrete solution, rather than accepting
                # an area computed using a provisional effective depth.
                if mrp['MRd_kNm'] + 1e-7 < mpos:
                    target_bot = max(target_bot, bot.area_mm2 * 1.02)
                if mrn['MRd_kNm'] + 1e-7 < mneg:
                    target_top = max(target_top, top.area_mm2 * 1.02)
        if last is not None:
            last['reinforcement_converged'] &= last['stir']['stirrup_status'] == 'OK'
            alternatives.append(last)
    if not alternatives:
        raise ValueError('Geometria incompatível com as duas faces de armadura.')
    return min(alternatives, key=lambda r: (
        not r['reinforcement_converged'], r['bot'].area_mm2 + r['top'].area_mm2,
        max(r['bot'].layers, r['top'].layers),
        {8.0: 0, 10.0: 1, 6.0: 2}[r['reinforcement_stirrup_assumed_mm']],
        -r['stir']['s_st_mm']))
