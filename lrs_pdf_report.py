# lrs_pdf_report.py
# Génération du rapport PDF professionnel LRS™
# Utilise reportlab — fond sombre, branding LRS

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, HRFlowable, KeepTogether
)

PAGE_W, PAGE_H = A4

# ── Palette LRS ─────────────────────────────────────────────
C_BG      = colors.HexColor("#0d0d1a")
C_SURFACE = colors.HexColor("#1a1a2e")
C_SURFACE2= colors.HexColor("#16213e")
C_BORDER  = colors.HexColor("#2a2a4a")
C_RED     = colors.HexColor("#FF4444")
C_ORANGE  = colors.HexColor("#FF8C00")
C_GREEN   = colors.HexColor("#22c55e")
C_ACCENT  = colors.HexColor("#6366f1")
C_WHITE   = colors.HexColor("#ffffff")
C_LIGHT   = colors.HexColor("#cccccc")
C_GRAY    = colors.HexColor("#888888")

def _score_color(v, mx=5):
    ratio = v / mx
    if ratio <= 0.45: return "#FF4444"
    if ratio <= 0.65: return "#FF8C00"
    return "#22c55e"

def _bar(v, mx=5, n=10):
    f = round(v / mx * n)
    return "█" * f + "░" * (n - f)

def _s(name, **kw):
    """Crée un ParagraphStyle rapide."""
    base = dict(fontName="Helvetica", fontSize=9, textColor=C_LIGHT, leading=13, spaceAfter=2)
    base.update(kw)
    return ParagraphStyle(name, **base)

def _card(rows, left_border_color=None, bg=None):
    """Table carte avec fond et bordure gauche optionnelle."""
    bg = bg or C_SURFACE
    t = Table(rows, colWidths=[17*cm])
    style = [
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("RIGHTPADDING",  (0,0),(-1,-1), 12),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
    ]
    if left_border_color:
        style.append(("LINEBEFORE", (0,0),(-1,-1), 4, left_border_color))
    t.setStyle(TableStyle(style))
    return t


def generate_pdf_report(result: dict, meta: dict) -> bytes:
    """Génère un rapport PDF LRS professionnel. Retourne les bytes du PDF."""

    buf = io.BytesIO()
    c_  = result.get("_c", {})
    why = result.get("why_this_score", {})
    mm_ = result.get("message_match", {})
    fp  = result.get("fix_plan", {})
    rw  = result.get("rewrite", {})
    ads = result.get("ads", {})
    lrs = result.get("lrs", {})

    score    = c_.get("score", 0)
    hook     = c_.get("hook", 0)
    offer    = c_.get("offer", 0)
    trust    = c_.get("trust", 0)
    friction = c_.get("friction", 0)
    risk     = c_.get("risk", "High")
    decision = c_.get("decision", "Do NOT launch")

    sc_hex  = _score_color(score, 20)
    version = meta.get("version", "2.3")

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm,   bottomMargin=2.2*cm,
    )
    W = doc.width
    story = []

    # ── FOND NOIR + FOOTER sur chaque page ──────────────────
    def _page_deco(canvas, doc_obj):
        canvas.saveState()
        # fond
        canvas.setFillColor(C_BG)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # ligne footer
        canvas.setStrokeColor(C_BORDER)
        canvas.line(1.5*cm, 1.6*cm, PAGE_W - 1.5*cm, 1.6*cm)
        # texte footer
        canvas.setFillColor(C_GRAY)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(1.5*cm, 1.1*cm, f"LRS™ Launch Risk System V{version} — Rapport confidentiel")
        canvas.drawRightString(PAGE_W - 1.5*cm, 1.1*cm, f"Page {doc_obj.page}")
        canvas.restoreState()

    # ════════════════════════════════════════════════════════
    # PAGE 1 — COVER
    # ════════════════════════════════════════════════════════

    # Header bar
    hdr = Table([[
        Paragraph("<b>🚦 LRS™</b> — Launch Risk System",
                  _s("hdr", fontSize=11, fontName="Helvetica-Bold", textColor=C_WHITE)),
        Paragraph(f"V{version}  |  {meta.get('timestamp','')}",
                  _s("hdrr", fontSize=8, textColor=C_GRAY, alignment=TA_RIGHT)),
    ]], colWidths=[W*0.6, W*0.4])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE),
        ("LEFTPADDING",   (0,0),(-1,-1), 14), ("RIGHTPADDING", (0,0),(-1,-1), 14),
        ("TOPPADDING",    (0,0),(-1,-1), 10), ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("LINEBELOW",     (0,0),(-1,-1), 2, C_ACCENT),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [Spacer(1, 0.3*cm), hdr, Spacer(1, 0.8*cm)]

    # Big Score
    dec_emoji = "🔴" if risk=="High" else "🟡" if risk=="Moderate" else "🟢"
    score_block = Table([
        [Paragraph(f"<font color='{sc_hex}'><b>{score}</b></font><font color='#444' size='20'>/20</font>",
                   _s("sb", fontSize=72, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=80))],
        [Paragraph(_bar(score, 20), _s("sbar", fontSize=16, fontName="Courier",
                   textColor=colors.HexColor(sc_hex), alignment=TA_CENTER))],
        [Paragraph(f"<font color='{sc_hex}'><b>{dec_emoji} {decision}</b></font>",
                   _s("sdec", fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=3))],
        [Paragraph(f"Risk Level : <font color='{sc_hex}'><b>{risk}</b></font>",
                   _s("srisk", fontSize=11, alignment=TA_CENTER, textColor=C_GRAY))],
    ], colWidths=[W])
    score_block.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#0f0f1a")),
        ("TOPPADDING",    (0,0),(-1,-1), 12), ("BOTTOMPADDING",(0,0),(-1,-1), 12),
        ("LEFTPADDING",   (0,0),(-1,-1), 20), ("RIGHTPADDING", (0,0),(-1,-1), 20),
        ("LINEBELOW",     (0,2),(0,2), 1, colors.HexColor(sc_hex)),
    ]))
    story += [score_block, Spacer(1, 0.6*cm)]

    # 4 métriques breakdown
    metrics_row = []
    for label, val in [("Hook", hook), ("Offer", offer), ("Trust", trust), ("Friction", friction)]:
        hx = _score_color(val)
        cell = Table([
            [Paragraph(f"<font color='{hx}'><b>{val}/5</b></font>",
                       _s(f"mv{label}", fontSize=24, fontName="Helvetica-Bold",
                          alignment=TA_CENTER, textColor=colors.HexColor(hx)))],
            [Paragraph(label, _s(f"ml{label}", fontSize=8, textColor=C_GRAY, alignment=TA_CENTER))],
            [Paragraph(_bar(val), _s(f"mb{label}", fontSize=8, fontName="Courier",
                       textColor=colors.HexColor(hx), alignment=TA_CENTER))],
        ], colWidths=[W/4 - 0.3*cm])
        cell.setStyle(TableStyle([
            ("BACKGROUND",  (0,0),(-1,-1), C_SURFACE),
            ("TOPPADDING",  (0,0),(-1,-1), 8), ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ]))
        metrics_row.append(cell)

    t_metrics = Table([metrics_row], colWidths=[W/4]*4)
    t_metrics.setStyle(TableStyle([
        ("GRID", (0,0),(-1,-1), 0.5, C_BORDER),
        ("TOPPADDING", (0,0),(-1,-1), 0), ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("LEFTPADDING",(0,0),(-1,-1), 0), ("RIGHTPADDING", (0,0),(-1,-1), 0),
    ]))
    story += [t_metrics, Spacer(1, 0.5*cm)]

    # Meta info
    url = meta.get("url","N/A")
    if len(url) > 70: url = url[:67]+"..."
    page_type = lrs.get("page_type", meta.get("page_type","N/A"))
    if len(str(page_type)) > 55: page_type = str(page_type)[:52]+"..."

    meta_rows = [
        ["URL analysée", url],
        ["Mode d'audit", meta.get("mode","")],
        ["Plateforme", meta.get("platform","")],
        ["Type d'offre", meta.get("offer_type","")],
        ["Type de marque", meta.get("brand_type","")],
        ["Type de page", page_type],
        ["CVR actuel estimé", c_.get("cvr_cur","")],
        ["CVR post-fix estimé", c_.get("cvr_fix","")],
        ["Uplift potentiel", c_.get("cvr_up","")],
    ]
    t_meta = Table(
        [[Paragraph(f"<b>{r}</b>", _s("mk", fontSize=8, textColor=C_GRAY)),
          Paragraph(str(v),        _s("mv", fontSize=8, textColor=C_LIGHT))]
         for r,v in meta_rows],
        colWidths=[W*0.28, W*0.72]
    )
    t_meta.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [C_SURFACE, C_SURFACE2]),
        ("LEFTPADDING",  (0,0),(-1,-1), 10), ("RIGHTPADDING", (0,0),(-1,-1), 10),
        ("TOPPADDING",   (0,0),(-1,-1), 5),  ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LINEBELOW",    (0,0),(-1,-1), 0.3, C_BORDER),
    ]))
    story += [t_meta, PageBreak()]

    # ════════════════════════════════════════════════════════
    # PAGE 2 — ANALYSE DÉTAILLÉE
    # ════════════════════════════════════════════════════════

    story += [
        Paragraph("Analyse Détaillée", _s("h1", fontSize=16, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=4)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
    ]

    for key, label, val in [
        ("hook_detail","Hook",hook),("offer_detail","Offer",offer),
        ("trust_detail","Trust",trust),("friction_detail","Friction",friction),
    ]:
        detail = why.get(key,"")
        if not detail: continue
        hx = _score_color(val)
        story.append(KeepTogether([
            _card([
                [Paragraph(f"<font color='{hx}'><b>{label} — {val}/5</b></font>  "
                           f"<font color='#444444'>{_bar(val)}</font>",
                           _s(f"sh{label}", fontSize=11, fontName="Helvetica-Bold"))],
                [Paragraph(detail, _s(f"sd{label}", fontSize=9, textColor=C_LIGHT, leading=13))],
            ], left_border_color=colors.HexColor(hx), bg=colors.HexColor("#13131f")),
            Spacer(1, 0.25*cm),
        ]))

    # Top 3 + Critical Gaps
    top3 = why.get("top_3_reasons", [])
    gaps = why.get("critical_gaps", [])
    if top3 or gaps:
        top3_txt = "<br/>".join([f"• {r}" for r in top3])
        gaps_txt = "<br/>".join([f"⚠ {g}" for g in gaps])
        t_2col = Table([[
            Paragraph(f"<b><font color='#FF8C00'>Top 3 Raisons</font></b><br/><br/>"
                      f"<font color='#cccccc'>{top3_txt}</font>",
                      _s("t3", fontSize=9, leading=14)),
            Paragraph(f"<b><font color='#FF4444'>Critical Gaps</font></b><br/><br/>"
                      f"<font color='#cccccc'>{gaps_txt}</font>",
                      _s("cg", fontSize=9, leading=14)),
        ]], colWidths=[W/2-0.2*cm, W/2-0.2*cm])
        t_2col.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), C_SURFACE),
            ("LEFTPADDING",  (0,0),(-1,-1), 14), ("RIGHTPADDING", (0,0),(-1,-1), 14),
            ("TOPPADDING",   (0,0),(-1,-1), 10), ("BOTTOMPADDING",(0,0),(-1,-1), 10),
            ("LINEBETWEEN",  (0,0),(1,-1), 0.5, C_BORDER),
        ]))
        story += [Spacer(1, 0.2*cm), t_2col, PageBreak()]

    # ════════════════════════════════════════════════════════
    # PAGE 3 — PLAN D'ACTION
    # ════════════════════════════════════════════════════════

    story += [
        Paragraph("Plan d'Action Priorisé", _s("h1p", fontSize=16, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=4)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
    ]

    # Top Priority
    tp = fp.get("top_priority_action", {})
    if tp and tp.get("what"):
        story.append(KeepTogether([
            _card([
                [Paragraph("🎯  ACTION PRIORITAIRE #1",
                           _s("tph", fontSize=11, fontName="Helvetica-Bold", textColor=C_RED))],
                [Paragraph(f"<b>{tp.get('what','')}</b>",
                           _s("tpw", fontSize=10, textColor=C_WHITE))],
                [Paragraph(f"<b>Comment exactement :</b> {tp.get('how_exactly','')}",
                           _s("tph2", fontSize=9, textColor=C_LIGHT, leading=13))],
                [Paragraph(f"<b>Impact :</b> {tp.get('expected_impact','')}   "
                           f"<b>Temps :</b> {tp.get('time_estimate','')}",
                           _s("tpt", fontSize=8, textColor=C_GRAY))],
            ], left_border_color=C_RED, bg=colors.HexColor("#1f0808")),
            Spacer(1, 0.35*cm),
        ]))

    # Quick Wins
    qws = fp.get("quick_wins", [])
    if qws:
        story += [Paragraph("⚡  Quick Wins  (moins d'1h)",
                            _s("qwh", fontSize=12, fontName="Helvetica-Bold", textColor=C_GREEN, spaceAfter=5))]
        for qw in qws:
            story.append(KeepTogether([
                _card([
                    [Paragraph(f"<b>{qw.get('what','')}</b>",
                               _s("qwt", fontSize=10, textColor=C_GREEN))],
                    [Paragraph(qw.get("how_exactly",""),
                               _s("qwb", fontSize=9, textColor=C_LIGHT, leading=13))],
                    [Paragraph(f"Impact : {qw.get('expected_impact','')}  |  Temps : {qw.get('time_estimate','<1h')}",
                               _s("qwm", fontSize=8, textColor=C_GRAY))],
                ], left_border_color=C_GREEN, bg=colors.HexColor("#0a1f0a")),
                Spacer(1, 0.2*cm),
            ]))

    # Long Term
    lts = fp.get("long_term", [])
    if lts:
        story += [Spacer(1, 0.2*cm),
                  Paragraph("🏗️  Améliorations Long Terme",
                            _s("lth", fontSize=12, fontName="Helvetica-Bold", textColor=C_ORANGE, spaceAfter=5))]
        for lt in lts:
            story.append(KeepTogether([
                _card([
                    [Paragraph(f"<b>{lt.get('what','')}</b>",
                               _s("ltt", fontSize=10, textColor=C_ORANGE))],
                    [Paragraph(lt.get("how_exactly",""),
                               _s("ltb", fontSize=9, textColor=C_LIGHT, leading=13))],
                    [Paragraph(f"Impact : {lt.get('expected_impact','')}  |  Temps : {lt.get('time_estimate','')}",
                               _s("ltm", fontSize=8, textColor=C_GRAY))],
                ], left_border_color=C_ORANGE, bg=colors.HexColor("#1f1000")),
                Spacer(1, 0.2*cm),
            ]))

    # A/B Tests
    abt = fp.get("ab_tests", [])
    if abt:
        story += [Spacer(1, 0.2*cm),
                  Paragraph("🧪  Tests A/B",
                            _s("abh2", fontSize=12, fontName="Helvetica-Bold", textColor=C_ACCENT, spaceAfter=5))]
        for ab in abt:
            ab_inner = Table([[
                Paragraph(f"<b>A :</b> {ab.get('variant_a','')}",
                          _s("aba", fontSize=9, textColor=C_LIGHT, leading=12)),
                Paragraph(f"<b>B :</b> {ab.get('variant_b','')}",
                          _s("abb", fontSize=9, textColor=C_LIGHT, leading=12)),
            ]], colWidths=[W/2-1.5*cm, W/2-1.5*cm])
            ab_inner.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
            story.append(KeepTogether([
                _card([
                    [Paragraph(f"<b>Hypothèse :</b> {ab.get('hypothesis','')}",
                               _s("abhy", fontSize=9, textColor=C_WHITE))],
                    [ab_inner],
                    [Paragraph(f"Métrique : {ab.get('success_metric','')}",
                               _s("abm", fontSize=8, textColor=C_GRAY))],
                ], left_border_color=C_ACCENT),
                Spacer(1, 0.2*cm),
            ]))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # PAGE 4 — REWRITE & ADS
    # ════════════════════════════════════════════════════════

    story += [
        Paragraph("Rewrite Recommandations", _s("h1r", fontSize=16, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=4)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
    ]

    rw_items = [
        ("Headline",       rw.get("headline","")),
        ("Subheadline",    rw.get("subheadline","")),
        ("CTA Principal",  rw.get("cta_primary","")),
        ("Garantie",       rw.get("guarantee","")),
        ("Proof Block",    rw.get("proof_block","")),
    ]
    for label, val in rw_items:
        if not val: continue
        t_row = Table([[
            Paragraph(f"<b>{label}</b>", _s(f"rl{label}", fontSize=8, textColor=C_GRAY)),
            Paragraph(str(val),          _s(f"rv{label}", fontSize=9, textColor=C_WHITE)),
        ]], colWidths=[W*0.22, W*0.78])
        t_row.setStyle(TableStyle([
            ("ROWBACKGROUNDS",(0,0),(-1,-1), [C_SURFACE, C_SURFACE2]),
            ("LEFTPADDING",  (0,0),(-1,-1), 10), ("RIGHTPADDING",(0,0),(-1,-1),10),
            ("TOPPADDING",   (0,0),(-1,-1), 6),  ("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("LINEBELOW",    (0,0),(-1,-1), 0.3, C_BORDER),
        ]))
        story.append(t_row)

    bullets = rw.get("hero_bullets", [])
    if bullets:
        story += [Spacer(1,0.2*cm), Paragraph("<b>Hero Bullets</b>", _s("bh", fontSize=9, textColor=C_GRAY))]
        for b in bullets:
            story.append(Paragraph(f"→ {b}", _s("bi", fontSize=9, textColor=C_LIGHT, leftIndent=12, leading=13)))

    stack = rw.get("offer_stack", [])
    if stack:
        story += [Spacer(1,0.2*cm), Paragraph("<b>Offer Stack</b>", _s("osh", fontSize=9, textColor=C_GRAY))]
        for o in stack:
            story.append(Paragraph(f"✓ {o}", _s("osi", fontSize=9, textColor=C_GREEN, leftIndent=12)))

    # ADS
    story += [
        Spacer(1, 0.5*cm),
        Paragraph("Ad Creative Recommendations", _s("h1a", fontSize=16, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=4)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=8),
    ]

    angles = ads.get("angles", [])
    if angles:
        story.append(Paragraph("<b>Angles</b>", _s("angh", fontSize=10, textColor=C_GRAY)))
        for a2 in angles:
            if isinstance(a2, dict):
                story.append(Paragraph(
                    f"<b>{a2.get('angle','')}</b> — {a2.get('rationale','')}",
                    _s("angi", fontSize=9, textColor=C_LIGHT, leftIndent=10, leading=13)
                ))

    hooks = ads.get("hooks", [])
    if hooks:
        story += [Spacer(1,0.2*cm), Paragraph("<b>Hooks</b>", _s("hkh", fontSize=10, textColor=C_GRAY))]
        for h in hooks:
            if isinstance(h, dict):
                story.append(Paragraph(
                    f"[{h.get('platform','')}/{h.get('type','')}]  {h.get('hook','')}",
                    _s("hki", fontSize=9, fontName="Courier", textColor=C_LIGHT, leftIndent=10)
                ))

    variants = ads.get("variants", [])
    if variants:
        story += [Spacer(1,0.2*cm), Paragraph("<b>Variantes Créatives</b>", _s("varh", fontSize=10, textColor=C_GRAY))]
        for i, v in enumerate(variants, 1):
            story.append(KeepTogether([
                _card([
                    [Paragraph(f"<b>Variante {i} — {v.get('platform','')}</b>",
                               _s(f"vh{i}", fontSize=9, fontName="Helvetica-Bold", textColor=C_ACCENT))],
                    [Paragraph(f"<b>Headline :</b> {v.get('headline','')}",   _s(f"vhl{i}", fontSize=9, textColor=C_WHITE))],
                    [Paragraph(f"<b>Text :</b> {v.get('primary_text','')}",   _s(f"vpt{i}", fontSize=9, textColor=C_LIGHT, leading=12))],
                    [Paragraph(f"<b>CTA :</b> {v.get('cta','')}",             _s(f"vca{i}", fontSize=9, textColor=C_GREEN))],
                ], left_border_color=C_ACCENT),
                Spacer(1, 0.2*cm),
            ]))

    ugc = ads.get("script_ugc_20s","")
    if ugc:
        story += [
            Spacer(1,0.2*cm),
            Paragraph("<b>Script UGC 20-30s</b>", _s("ugch", fontSize=10, textColor=C_GRAY)),
            _card([[Paragraph(ugc, _s("ugcb", fontSize=9, fontName="Courier", textColor=C_LIGHT, leading=13))]],
                  left_border_color=C_ACCENT, bg=colors.HexColor("#0f0f1a")),
        ]

    doc.build(story, onFirstPage=_page_deco, onLaterPages=_page_deco)
    return buf.getvalue()
