import io
import os
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
FONTS_DIR = Path(__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont('F',  FONTS_DIR / "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont('FB', FONTS_DIR / "DejaVuSans-Bold.ttf"))
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

# ── палитра ──────────────────────────────────────────────────
C_DARK        = colors.HexColor('#1a1a2e')
C_GOLD        = colors.HexColor('#c89b3c')
C_GOLD_LINE   = colors.HexColor('#e0b456')
C_WHITE_SIDE  = colors.HexColor('#f0f0f0')
C_BLUE_SIDE   = colors.HexColor('#2563eb')
C_WIN_BAR     = colors.HexColor('#c89b3c')
C_CONNECTOR   = colors.HexColor('#d4aa5a')
C_BORDER      = colors.HexColor('#e9ecef')
C_TEXT_DARK   = colors.HexColor('#111827')
C_TEXT_GREY   = colors.HexColor('#9ca3af')
C_TEXT_BLUE_L = colors.HexColor('#93c5fd')

# ── размеры ──────────────────────────────────────────────────
CARD_W    = 46 * mm
ROW_H     = 8.5 * mm
CARD_H    = ROW_H * 2
WIN_BAR_W = 2.2 * mm
CARD_R    = 1.8 * mm
COL_GAP   = 16 * mm
HEADER_H  = 28 * mm
FOOTER_H  = 10 * mm
LABEL_H   = 7  * mm


def _rgb(col):
    return col.red, col.green, col.blue

def _fill(c, col):
    c.setFillColorRGB(*_rgb(col))

def _stroke(c, col):
    c.setStrokeColorRGB(*_rgb(col))

def _last(ath):
    return (ath.get('last_name') or 'TBD').upper() if ath else 'TBD'

def _first(ath):
    return (ath.get('first_name') or '') if ath else ''

def _fmt(sec):
    if not sec and sec != 0:
        return ''
    return f"{int(sec)//60}:{int(sec)%60:02d}"


# ────────────────────────────────────────────────────────────
# Карточка одного боя  (x, y — нижний левый угол)
# ────────────────────────────────────────────────────────────
def _draw_card(c, x, y, white_ath, blue_ath, winner_id, result=None):
    w   = CARD_W
    mid = y + ROW_H   # граница белый/синий

    # фоны
    _fill(c, C_WHITE_SIDE)
    c.rect(x, mid, w, ROW_H, fill=1, stroke=0)
    _fill(c, C_BLUE_SIDE)
    c.rect(x, y, w, ROW_H, fill=1, stroke=0)

    # разделитель
    _stroke(c, C_BORDER)
    c.setLineWidth(0.3)
    c.line(x, mid, x + w, mid)

    # золотая полоска победителя
    white_id = (white_ath or {}).get('id')
    blue_id  = (blue_ath  or {}).get('id')
    if winner_id and winner_id == white_id:
        _fill(c, C_WIN_BAR)
        c.rect(x, mid, WIN_BAR_W, ROW_H, fill=1, stroke=0)
    if winner_id and winner_id == blue_id:
        _fill(c, C_WIN_BAR)
        c.rect(x, y, WIN_BAR_W, ROW_H, fill=1, stroke=0)

    tx = x + WIN_BAR_W + 1.5 * mm

    # белый угол: фамилия
    c.setFont('FB', 6)
    is_w_loser = winner_id and white_id and winner_id != white_id
    _fill(c, C_TEXT_GREY if is_w_loser else C_TEXT_DARK)
    c.drawString(tx, mid + ROW_H * 0.52, _last(white_ath)[:20])
    # имя
    c.setFont('F', 4.8)
    _fill(c, C_TEXT_GREY)
    c.drawString(tx, mid + 1.5 * mm, _first(white_ath)[:20])

    # синий угол: фамилия
    c.setFont('FB', 6)
    is_b_loser = winner_id and blue_id and winner_id != blue_id
    _fill(c, C_TEXT_BLUE_L if is_b_loser else colors.white)
    c.drawString(tx, y + ROW_H * 0.52, _last(blue_ath)[:20])
    # имя
    c.setFont('F', 4.8)
    _fill(c, C_TEXT_BLUE_L)
    c.drawString(tx, y + 1.5 * mm, _first(blue_ath)[:20])

    # тип победы / время (справа)
    if result:
        rx = x + w - 1.2 * mm
        c.setFont('F', 4)
        _fill(c, C_TEXT_GREY)
        vt = result.get('victory_type', '')
        if vt:
            c.drawRightString(rx, mid + ROW_H * 0.45, vt[:9])
        dur = _fmt(result.get('fight_duration'))
        if dur:
            c.drawRightString(rx, y + ROW_H * 0.45, dur)

    # бордюр
    _stroke(c, C_BORDER)
    _fill(c, colors.Color(0, 0, 0, alpha=0))
    c.setLineWidth(0.5)
    c.roundRect(x, y, w, CARD_H, CARD_R, fill=0, stroke=1)


# ────────────────────────────────────────────────────────────
# Карточка чемпиона
# ────────────────────────────────────────────────────────────
def _draw_champion(c, x, y, ath):
    w = CARD_W + 4 * mm
    _fill(c, colors.HexColor('#fffdf5'))
    _stroke(c, C_GOLD)
    c.setLineWidth(1.5)
    c.roundRect(x, y, w, CARD_H, CARD_R, fill=1, stroke=1)

    c.setFont('FB', 7)
    _fill(c, C_GOLD)
    c.drawString(x + 3 * mm, y + CARD_H * 0.62, _last(ath) if ath else 'TBD')
    c.setFont('F', 5.5)
    _fill(c, C_TEXT_GREY)
    c.drawString(x + 3 * mm, y + CARD_H * 0.28, _first(ath) if ath else '')


# ────────────────────────────────────────────────────────────
# Соединительные линии (логика 1-в-1 с Vue SVG)
# ────────────────────────────────────────────────────────────
def _draw_connectors(c, round_positions):
    _stroke(c, C_CONNECTOR)
    c.setLineWidth(1.0)
    c.setLineCap(1)

    for ri in range(len(round_positions) - 1):
        src = round_positions[ri]
        tgt = round_positions[ri + 1]

        for pi in range(len(tgt)):
            tx, ty   = tgt[pi]
            tgt_mid  = ty + CARD_H / 2
            i1, i2   = pi * 2, pi * 2 + 1

            if i1 >= len(src):
                continue

            x1, y1   = src[i1]
            mid1     = y1 + CARD_H / 2
            right_x  = x1 + CARD_W
            bridge_x = (right_x + tx) / 2

            # карточка 1 → bridge
            p = c.beginPath()
            p.moveTo(right_x, mid1)
            p.lineTo(bridge_x, mid1)
            c.drawPath(p, stroke=1, fill=0)

            if i2 < len(src):
                x2, y2 = src[i2]
                mid2   = y2 + CARD_H / 2

                # карточка 2 → bridge
                p = c.beginPath()
                p.moveTo(x2 + CARD_W, mid2)
                p.lineTo(bridge_x, mid2)
                c.drawPath(p, stroke=1, fill=0)

                # вертикальная перемычка
                p = c.beginPath()
                p.moveTo(bridge_x, mid1)
                p.lineTo(bridge_x, mid2)
                c.drawPath(p, stroke=1, fill=0)

                bridge_y = (mid1 + mid2) / 2
            else:
                bridge_y = mid1

            # bridge → следующая карточка
            p = c.beginPath()
            p.moveTo(bridge_x, bridge_y)
            p.lineTo(tx, tgt_mid)
            c.drawPath(p, stroke=1, fill=0)

            # кружки
            _fill(c, C_CONNECTOR)
            for dx, dy in [(bridge_x, mid1), (bridge_x, bridge_y)]:
                c.circle(dx, dy, 1.0 * mm, fill=1, stroke=0)
            if i2 < len(src):
                c.circle(bridge_x, src[i2][1] + CARD_H / 2, 1.0 * mm, fill=1, stroke=0)


# ────────────────────────────────────────────────────────────
# Шапка страницы
# ────────────────────────────────────────────────────────────
def _draw_header(c, pw, ph, t_name, cat_name, date_str, city, tatami, competitors):
    _fill(c, C_DARK)
    c.rect(0, ph - HEADER_H, pw, HEADER_H, fill=1, stroke=0)

    _stroke(c, C_GOLD_LINE)
    c.setLineWidth(1.2)
    c.line(0, ph - HEADER_H, pw, ph - HEADER_H)

    c.setFont('FB', 11)
    _fill(c, C_GOLD)
    c.drawString(10 * mm, ph - 11 * mm, t_name)

    c.setFont('F', 8)
    _fill(c, colors.HexColor('#e5e7eb'))
    c.drawString(10 * mm, ph - 19 * mm, f'{city}  ·  {date_str}')

    c.setFont('FB', 16)
    _fill(c, colors.white)
    c.drawRightString(pw - 10 * mm, ph - 14 * mm, cat_name)

    c.setFont('F', 7)
    _fill(c, C_TEXT_GREY)
    c.drawRightString(pw - 10 * mm, ph - 22 * mm,
                      f'Татами: {tatami}    Участников: {competitors}')


# ────────────────────────────────────────────────────────────
# Колонтитул
# ────────────────────────────────────────────────────────────
def _draw_footer(c, pw, t_name, page_num):
    _stroke(c, C_GOLD_LINE)
    c.setLineWidth(0.5)
    c.line(10 * mm, FOOTER_H - 1 * mm, pw - 10 * mm, FOOTER_H - 1 * mm)
    c.setFont('F', 6)
    _fill(c, C_TEXT_GREY)
    c.drawString(10 * mm, FOOTER_H - 5 * mm, t_name)
    c.drawRightString(pw - 10 * mm, FOOTER_H - 5 * mm, f'Стр. {page_num}')


# ────────────────────────────────────────────────────────────
# Страница: турнирная сетка
# ────────────────────────────────────────────────────────────
def _bracket_page(c, pw, ph, t_name, cat, date_str, city, page_num):
    cat_name    = cat.get('name', '')
    tatami      = cat.get('tatami', '—')
    competitors = cat.get('competitors', 0)
    fights      = cat.get('fights', [])
    results     = cat.get('results', [])
    res_map     = {r['fight_id']: r for r in results}

    main_fights = [f for f in fights
                   if not f.get('type_bracket') or f.get('type_bracket') == 'MAIN']

    _draw_header(c, pw, ph, t_name, cat_name, date_str, city, tatami, competitors)
    _draw_footer(c, pw, t_name, page_num)

    if not main_fights:
        c.setFont('F', 9)
        _fill(c, C_TEXT_GREY)
        c.drawCentredString(pw / 2, ph / 2, 'Схватки ещё не добавлены')
        return

    # группируем по раундам
    rounds_map = {}
    for f in main_fights:
        r = f.get('round') or f.get('round_number', 1)
        rounds_map.setdefault(r, []).append(f)

    max_round   = max(rounds_map)
    stage_lbl   = ['1/32', '1/16', '1/8', '1/4', 'Полуфинал', 'Финал']
    offset      = max(0, len(stage_lbl) - max_round)

    def rlabel(ri):
        if ri == max_round:
            return 'Финал'
        idx = offset + ri - 1
        return stage_lbl[idx] if idx < len(stage_lbl) else f'Раунд {ri}'

    # область рисования
    area_top    = ph - HEADER_H - 4 * mm
    area_bottom = FOOTER_H + 4 * mm

    total_cols  = max_round + 1
    bracket_w   = total_cols * CARD_W + (total_cols - 1) * COL_GAP
    start_x     = max(8 * mm, (pw - bracket_w) / 2)

    # метки раундов
    lbl_y = area_top - LABEL_H
    for ri in range(1, max_round + 1):
        cx = start_x + (ri - 1) * (CARD_W + COL_GAP)
        c.setFont('FB', 5.5)
        _fill(c, C_GOLD)
        c.drawCentredString(cx + CARD_W / 2, lbl_y + 1 * mm, rlabel(ri).upper())
        _stroke(c, colors.HexColor('#e0b45660'))
        c.setLineWidth(0.3)
        c.line(cx, lbl_y, cx + CARD_W, lbl_y)

    champ_x = start_x + max_round * (CARD_W + COL_GAP)
    c.setFont('FB', 5.5)
    _fill(c, C_GOLD)
    c.drawCentredString(champ_x + (CARD_W + 4 * mm) / 2, lbl_y + 1 * mm, 'ЧЕМПИОН')
    _stroke(c, colors.HexColor('#e0b45660'))
    c.setLineWidth(0.3)
    c.line(champ_x, lbl_y, champ_x + CARD_W + 4 * mm, lbl_y)

    draw_top    = lbl_y - 3 * mm
    round_positions = []

    for ri in range(1, max_round + 1):
        col_fights = sorted(rounds_map.get(ri, []),
                            key=lambda f: f.get('fight_number') or f.get('id', 0))
        n    = len(col_fights)
        cx   = start_x + (ri - 1) * (CARD_W + COL_GAP)
        col_h = draw_top - area_bottom
        step  = col_h / n if n else col_h

        positions = []
        for fi, fight in enumerate(col_fights):
            slot_cy = draw_top - step * fi - step / 2
            card_y  = slot_cy - CARD_H / 2
            res     = res_map.get(fight['id'])
            win_id  = res.get('winner_id') if res else None
            _draw_card(c, cx, card_y,
                       fight.get('white_athlete'),
                       fight.get('blue_athlete'),
                       win_id, res)
            positions.append((cx, card_y))

        round_positions.append(positions)

    _draw_connectors(c, round_positions)

    # чемпион
    champ_ath = None
    if max_round in rounds_map:
        finals = sorted(rounds_map[max_round],
                        key=lambda f: f.get('fight_number') or 0)
        if finals:
            fin = finals[0]
            res = res_map.get(fin['id'])
            if res:
                wid = res.get('winner_id')
                wa  = fin.get('white_athlete') or {}
                ba  = fin.get('blue_athlete')  or {}
                champ_ath = wa if wa.get('id') == wid else (ba if ba.get('id') == wid else None)

    if round_positions and round_positions[-1]:
        last = round_positions[-1]
        ys   = [p[1] for p in last]
        cy   = (min(ys) + max(ys) + CARD_H) / 2 - CARD_H / 2

        # линия финал → чемпион
        fx, fy = last[0]
        _stroke(c, C_CONNECTOR)
        c.setLineWidth(1.0)
        p = c.beginPath()
        p.moveTo(fx + CARD_W, fy + CARD_H / 2)
        p.lineTo(champ_x, cy + CARD_H / 2)
        c.drawPath(p, stroke=1, fill=0)

        _draw_champion(c, champ_x, cy, champ_ath)


# ────────────────────────────────────────────────────────────
# Страница: результаты + утешительные
# ────────────────────────────────────────────────────────────
def _results_page(c, pw, ph, t_name, cat, date_str, city, page_num):
    cat_name    = cat.get('name', '')
    tatami      = cat.get('tatami', '—')
    competitors = cat.get('competitors', 0)
    podium      = cat.get('podium', [])
    res_map     = {r['fight_id']: r for r in cat.get('results', [])}
    cons_fights = [f for f in cat.get('fights', [])
                   if f.get('type_bracket') and f.get('type_bracket') != 'MAIN']

    _draw_header(c, pw, ph, t_name, cat_name, date_str, city, tatami, competitors)
    _draw_footer(c, pw, t_name, page_num)

    cur_y = ph - HEADER_H - 10 * mm
    mx    = 10 * mm

    # итоговые места
    if podium:
        c.setFont('FB', 7)
        _fill(c, C_GOLD)
        c.drawString(mx, cur_y, 'ИТОГОВЫЕ РЕЗУЛЬТАТЫ')
        cur_y -= 7 * mm

        ROW     = 7 * mm
        col_pos = 12 * mm
        col_nm  = 65 * mm
        col_cl  = 55 * mm
        tw      = col_pos + col_nm + col_cl
        medal   = {1: '#FFD700', 2: '#C0C0C0', 3: '#CD7F32'}

        _fill(c, C_DARK)
        c.rect(mx, cur_y - ROW, tw, ROW, fill=1, stroke=0)
        c.setFont('FB', 6)
        _fill(c, C_GOLD)
        c.drawCentredString(mx + col_pos / 2,              cur_y - ROW + 2.2 * mm, 'МЕСТО')
        c.drawString(mx + col_pos + 2 * mm,                cur_y - ROW + 2.2 * mm, 'СПОРТСМЕН')
        c.drawString(mx + col_pos + col_nm + 2 * mm,       cur_y - ROW + 2.2 * mm, 'КЛУБ / СТРАНА')
        cur_y -= ROW

        for i, entry in enumerate(podium):
            pos  = entry.get('pos', '?')
            ath  = entry.get('athlete') or {}
            club = entry.get('club', '—')
            _fill(c, colors.HexColor('#f9f9f9') if i % 2 == 0 else colors.white)
            c.rect(mx, cur_y - ROW, tw, ROW, fill=1, stroke=0)
            if pos in medal:
                _fill(c, colors.HexColor(medal[pos]))
                c.rect(mx, cur_y - ROW, col_pos, ROW, fill=1, stroke=0)
            c.setFont('FB', 7)
            _fill(c, C_TEXT_DARK)
            c.drawCentredString(mx + col_pos / 2, cur_y - ROW + 2 * mm, str(pos))
            c.setFont('FB', 6.5)
            c.drawString(mx + col_pos + 2 * mm, cur_y - ROW + 2.2 * mm,
                         f"{_last(ath)} {_first(ath)}".strip()[:30])
            c.setFont('F', 5.5)
            _fill(c, C_TEXT_GREY)
            c.drawString(mx + col_pos + col_nm + 2 * mm, cur_y - ROW + 2.2 * mm, club[:26])
            _stroke(c, C_BORDER)
            c.setLineWidth(0.2)
            c.line(mx, cur_y - ROW, mx + tw, cur_y - ROW)
            cur_y -= ROW

        _stroke(c, C_BORDER)
        c.setLineWidth(0.5)
        c.rect(mx, cur_y, tw, ROW * (len(podium) + 1), stroke=1, fill=0)
        cur_y -= 10 * mm

    # утешительные бои
    if cons_fights:
        c.setFont('FB', 7)
        _fill(c, C_GOLD)
        c.drawString(mx, cur_y, 'УТЕШИТЕЛЬНЫЕ БОИ')
        cur_y -= 7 * mm

        groups = {}
        for f in cons_fights:
            bt = str(f.get('type_bracket', ''))
            g  = 'A' if 'GROUP_A' in bt else ('B' if 'GROUP_B' in bt else 'C')
            groups.setdefault(g, []).append(f)

        col_x = mx
        for gname, gfights in sorted(groups.items()):
            c.setFont('FB', 6)
            _fill(c, C_TEXT_GREY)
            c.drawString(col_x, cur_y, f'Группа {gname}')
            gy = cur_y - 4 * mm
            for fight in gfights:
                res    = res_map.get(fight['id'])
                win_id = res.get('winner_id') if res else None
                _draw_card(c, col_x, gy - CARD_H,
                           fight.get('white_athlete'),
                           fight.get('blue_athlete'),
                           win_id, res)
                gy -= CARD_H + 3 * mm
            col_x += CARD_W + 10 * mm


# ────────────────────────────────────────────────────────────
# ТОЧКА ВХОДА
# ────────────────────────────────────────────────────────────
def generate_tournament_pdf(tournament_data: dict) -> bytes:
    buf     = io.BytesIO()
    pw, ph  = landscape(A4)
    t       = tournament_data.get('tournament', {})
    t_name  = t.get('name', 'Турнир')
    t_date  = str(t.get('start_date', ''))
    t_city  = t.get('city', '')
    cats    = tournament_data.get('categories', [])

    cv = rl_canvas.Canvas(buf, pagesize=landscape(A4))
    cv.setTitle(t_name)

    page = 1
    for cat in cats:
        _bracket_page(cv, pw, ph, t_name, cat, t_date, t_city, page)
        cv.showPage()
        page += 1

        has_podium = bool(cat.get('podium'))
        has_cons   = any(f.get('type_bracket') and f.get('type_bracket') != 'MAIN'
                         for f in cat.get('fights', []))
        if has_podium or has_cons:
            _results_page(cv, pw, ph, t_name, cat, t_date, t_city, page)
            cv.showPage()
            page += 1

    cv.save()
    buf.seek(0)
    return buf.read()