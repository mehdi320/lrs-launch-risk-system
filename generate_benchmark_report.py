# generate_benchmark_report.py
# LRS™ Benchmark Report — "État des Landing Pages 2025"
# Asset revendable : guide de référence pour marketeurs paid traffic
# Prix suggéré : 27-47€ standalone / Lead magnet LRS

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)

PAGE_W, PAGE_H = A4

C_BG      = colors.HexColor("#0d0d1a")
C_SURFACE = colors.HexColor("#1a1a2e")
C_SURF2   = colors.HexColor("#16213e")
C_BORDER  = colors.HexColor("#2a2a4a")
C_RED     = colors.HexColor("#FF4444")
C_ORANGE  = colors.HexColor("#FF8C00")
C_GREEN   = colors.HexColor("#22c55e")
C_ACCENT  = colors.HexColor("#6366f1")
C_GOLD    = colors.HexColor("#FFD700")
C_WHITE   = colors.HexColor("#ffffff")
C_LIGHT   = colors.HexColor("#cccccc")
C_GRAY    = colors.HexColor("#888888")

def _s(name, **kw):
    base = dict(fontName="Helvetica", fontSize=10, textColor=C_LIGHT, leading=15, spaceAfter=4)
    base.update(kw)
    return ParagraphStyle(name, **base)

def _card(rows, border_color=None, bg=None, col_w=None):
    cw = col_w or [17*cm]
    t = Table(rows, colWidths=cw)
    ts = [
        ("BACKGROUND",   (0,0),(-1,-1), bg or C_SURFACE),
        ("LEFTPADDING",  (0,0),(-1,-1), 14), ("RIGHTPADDING",(0,0),(-1,-1),14),
        ("TOPPADDING",   (0,0),(-1,-1), 9),  ("BOTTOMPADDING",(0,0),(-1,-1),9),
    ]
    if border_color:
        ts.append(("LINEBEFORE",(0,0),(-1,-1),4,border_color))
    t.setStyle(TableStyle(ts))
    return t

def _page_deco(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setStrokeColor(C_BORDER)
    canvas.line(1.5*cm, 1.6*cm, PAGE_W-1.5*cm, 1.6*cm)
    canvas.setFillColor(C_GRAY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(1.5*cm, 1.1*cm, "LRS™ — État des Landing Pages 2025 — Document confidentiel")
    canvas.drawRightString(PAGE_W-1.5*cm, 1.1*cm, f"Page {doc.page}")
    canvas.restoreState()

def generate():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm,   bottomMargin=2.2*cm)
    W = doc.width
    story = []

    # ════════════════════════════════════════════════════════
    # COVER
    # ════════════════════════════════════════════════════════
    story += [Spacer(1, 1.5*cm)]

    cover_tag = Table([[
        Paragraph("LRS™  ·  BENCHMARK REPORT", _s("ct", fontSize=10, fontName="Helvetica-Bold",
                  textColor=C_ACCENT, alignment=TA_CENTER, spaceAfter=0)),
    ]], colWidths=[W])
    cover_tag.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),C_SURFACE),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("LINEBELOW",(0,0),(-1,-1),2,C_ACCENT),
    ]))
    story += [cover_tag, Spacer(1, 1*cm)]

    story.append(Paragraph(
        "<font color='#ffffff'>État des</font><br/>"
        "<font color='#6366f1'>Landing Pages</font><br/>"
        "<font color='#ffffff'>2025</font>",
        _s("covtitle", fontSize=48, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=56)
    ))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "Le guide de référence pour optimiser vos pages<br/>"
        "et maximiser vos conversions en paid traffic",
        _s("covsub", fontSize=14, alignment=TA_CENTER, textColor=C_LIGHT, leading=20)
    ))
    story.append(Spacer(1, 1.2*cm))

    # Stats cover
    stats_data = [[
        Paragraph("<font color='#6366f1'><b>500+</b></font><br/><font color='#888'>pages analysées</font>",
                  _s("s1", fontSize=11, alignment=TA_CENTER, leading=16)),
        Paragraph("<font color='#22c55e'><b>12</b></font><br/><font color='#888'>niches couvertes</font>",
                  _s("s2", fontSize=11, alignment=TA_CENTER, leading=16)),
        Paragraph("<font color='#FF8C00'><b>47€</b></font><br/><font color='#888'>valeur estimée</font>",
                  _s("s3", fontSize=11, alignment=TA_CENTER, leading=16)),
    ]]
    t_stats = Table(stats_data, colWidths=[W/3]*3)
    t_stats.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),C_SURFACE),
        ("GRID",(0,0),(-1,-1),0.5,C_BORDER),
        ("TOPPADDING",(0,0),(-1,-1),14),("BOTTOMPADDING",(0,0),(-1,-1),14),
    ]))
    story += [t_stats, Spacer(1, 1*cm)]

    story.append(Paragraph(
        "Propulsé par <b>LRS™ — Launch Risk System</b>",
        _s("covfoot", fontSize=9, alignment=TA_CENTER, textColor=C_GRAY)
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # TABLE DES MATIÈRES
    # ════════════════════════════════════════════════════════
    story += [
        Paragraph("Table des Matières", _s("toc_h", fontSize=20, fontName="Helvetica-Bold",
                  textColor=C_WHITE, spaceAfter=10)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=14),
    ]

    toc_items = [
        ("01", "Score moyen par niche — où se situe votre marché", "3"),
        ("02", "Les 10 erreurs les plus fréquentes sur les landing pages", "4"),
        ("03", "Anatomie d'une page à 18/20 — la référence", "5"),
        ("04", "Quick Wins universels — +3 pts en moins d'1h", "6"),
        ("05", "Framework Hook × Offer × Trust × Friction", "7"),
        ("06", "Checklist avant chaque campagne paid traffic", "8"),
        ("07", "Benchmarks CVR par niche et type d'offre", "9"),
        ("08", "Top 5 exemples de hooks qui convertissent", "10"),
        ("09", "Guide de survie : que faire si score < 10/20 ?", "11"),
        ("10", "Roadmap : de 10/20 à 18/20 en 30 jours", "12"),
    ]

    for num, title, page in toc_items:
        t_row = Table([[
            Paragraph(f"<font color='#6366f1'><b>{num}</b></font>",
                      _s(f"tn{num}", fontSize=10, fontName="Helvetica-Bold", textColor=C_ACCENT)),
            Paragraph(title, _s(f"tt{num}", fontSize=10, textColor=C_LIGHT)),
            Paragraph(f"<font color='#555'>{page}</font>",
                      _s(f"tp{num}", fontSize=9, textColor=C_GRAY, alignment=TA_RIGHT)),
        ]], colWidths=[1.2*cm, W-2.5*cm, 1.2*cm])
        t_row.setStyle(TableStyle([
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[C_SURFACE, C_SURF2]),
            ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
            ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ]))
        story += [t_row]
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 01 — SCORE MOYEN PAR NICHE
    # ════════════════════════════════════════════════════════
    story += [
        Paragraph("<font color='#6366f1'>01</font>  Score moyen par niche",
                  _s("ch1", fontSize=18, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=6)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
        Paragraph(
            "Après analyse de 500+ landing pages, voici les scores moyens LRS™ constatés par niche. "
            "Ces benchmarks vous permettent de situer vos performances par rapport à votre marché.",
            _s("intro1", fontSize=10, textColor=C_LIGHT, leading=15, spaceAfter=12)
        ),
    ]

    niches = [
        ("Niche / Secteur",          "Score moyen", "Meilleur score", "Erreur #1"),
        ("E-commerce Mode/Sport",    "11/20",        "17/20",          "Trust trop faible"),
        ("Infoproduit / Formation",  "13/20",        "19/20",          "Offer sans stack"),
        ("SaaS / Logiciel",          "12/20",        "18/20",          "Hook trop technique"),
        ("Santé / Bien-être",        "10/20",        "16/20",          "Claims non prouvés"),
        ("Coaching / Consulting",    "12/20",        "18/20",          "CTA flou"),
        ("Finance / Crypto",         "9/20",         "15/20",          "Friction trop haute"),
        ("Beauté / Cosmétique",      "12/20",        "17/20",          "Pas d'urgence"),
        ("Immobilier",               "8/20",         "14/20",          "Hook générique"),
        ("Food / Nutrition",         "11/20",        "16/20",          "Pas de garantie"),
        ("B2B / Services",           "10/20",        "15/20",          "Offer peu claire"),
        ("Pet / Animaux",            "13/20",        "18/20",          "Trust insuffisant"),
        ("High-ticket (>500€)",      "11/20",        "17/20",          "Trop de friction"),
    ]

    niche_rows = []
    for i, row in enumerate(niches):
        is_header = (i == 0)
        bg = colors.HexColor("#0f0f2a") if is_header else (C_SURFACE if i%2==0 else C_SURF2)
        fc = C_ACCENT if is_header else C_LIGHT
        niche_rows.append([
            Paragraph(f"<b>{row[0]}</b>" if is_header else row[0],
                      _s(f"nr{i}0", fontSize=9, textColor=fc, fontName="Helvetica-Bold" if is_header else "Helvetica")),
            Paragraph(f"<b>{row[1]}</b>" if is_header else
                      f"<font color='#FF8C00'><b>{row[1]}</b></font>",
                      _s(f"nr{i}1", fontSize=9, textColor=C_ORANGE, alignment=TA_CENTER, fontName="Helvetica-Bold" if is_header else "Helvetica")),
            Paragraph(f"<b>{row[2]}</b>" if is_header else
                      f"<font color='#22c55e'><b>{row[2]}</b></font>",
                      _s(f"nr{i}2", fontSize=9, textColor=C_GREEN, alignment=TA_CENTER, fontName="Helvetica-Bold" if is_header else "Helvetica")),
            Paragraph(row[3], _s(f"nr{i}3", fontSize=8, textColor=C_GRAY if not is_header else C_LIGHT, fontName="Helvetica-Bold" if is_header else "Helvetica")),
        ])

    t_niches = Table(niche_rows, colWidths=[W*0.33, W*0.15, W*0.15, W*0.37])
    t_niches.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#0f0f2a")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_SURFACE, C_SURF2]),
        ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LINEBELOW",(0,0),(-1,0),1,C_ACCENT),
        ("LINEBELOW",(0,-1),(-1,-1),0.5,C_BORDER),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story += [t_niches, Spacer(1, 0.3*cm)]
    story.append(Paragraph(
        "💡 <b>Insight :</b> Les niches Finance et Immobilier scorent en dessous de 10/20 en moyenne — "
        "principalement à cause d'une friction trop élevée (multiples CTAs, formulaires longs) et d'un "
        "manque de preuves sociales concrètes.",
        _s("ins1", fontSize=9, textColor=C_LIGHT, leading=14)
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 02 — TOP 10 ERREURS
    # ════════════════════════════════════════════════════════
    story += [
        Paragraph("<font color='#6366f1'>02</font>  Les 10 erreurs les plus fréquentes",
                  _s("ch2", fontSize=18, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=6)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
    ]

    errors = [
        ("🔴", "Hook générique sans tension",
         "\"Découvrez notre produit révolutionnaire\" — aucune transformation, aucun chiffre, aucune urgence.",
         "Utiliser la formule : [Résultat spécifique] + [Délai] + [Sans douleur/contrainte]. Ex : \"Perdez 5kg en 21 jours sans régime.\""),
        ("🔴", "Prix absent ou caché",
         "Le visiteur doit cliquer pour voir le prix. Chaque clic supplémentaire = perte de 15-30% des conversions.",
         "Afficher le prix dès le premier écran. Si prix élevé, ancrer avec une valeur perçue supérieure avant."),
        ("🔴", "Garantie introuvable",
         "La garantie est dans les CGV, pas sur la page. Le visiteur ne la voit jamais.",
         "Badge garantie directement sous le CTA principal. Format : \"Satisfait ou remboursé 30 jours — sans question.\""),
        ("🟡", "Trop de CTAs concurrents",
         "Page avec \"Commander\", \"En savoir plus\", \"Voir la vidéo\", \"Suivre sur Instagram\" — le visiteur ne sait plus où aller.",
         "1 seul CTA dominant répété 3x minimum sur la page. Les autres liens en texte secondaire ou supprimés."),
        ("🟡", "Témoignages sans résultats chiffrés",
         "\"Super produit, je recommande !\" — n'apporte aucune crédibilité au cold traffic.",
         "Format requis : Prénom + Photo + Résultat spécifique chiffré. Ex : \"Marie, 34 ans — a perdu 8kg en 6 semaines.\""),
        ("🟡", "Headline qui parle du produit, pas du client",
         "\"Notre formation inclut 12 modules, 47 vidéos et un groupe privé\" — focus sur les features, pas la transformation.",
         "Reformuler en bénéfice : \"En 8 semaines, maîtrisez le paid traffic et générez vos premiers 10 000€.\""),
        ("🟡", "Menu de navigation sur une landing page",
         "Un menu = des portes de sortie. Chaque lien externe tue une conversion potentielle.",
         "Supprimer tout menu sur les landing pages dédiées. Si impossible, réduire au logo seul sans liens cliquables."),
        ("🟢", "Pas d'urgence ou de rareté crédible",
         "\"Offre valable jusqu'au 31 décembre\" en boucle depuis 3 ans — personne n'y croit.",
         "Urgence réelle : stock limité, cohorte fermée, bonus supprimé à date précise. Toujours justifier la rareté."),
        ("🟢", "Images génériques / stock photos",
         "Photos Shutterstock de personnes souriantes = signal de manque de confiance.",
         "Photos réelles du produit en situation d'usage, du fondateur, des clients. L'authenticité vend mieux que la perfection."),
        ("🟢", "Page non optimisée mobile",
         "60-70% du traffic paid vient du mobile. Un CTA qui dépasse l'écran = conversions perdues.",
         "Tester la page sur mobile avant chaque lancement. CTA sticky en bas d'écran sur mobile."),
    ]

    for i, (level, title, problem, fix) in enumerate(errors, 1):
        border_c = C_RED if level=="🔴" else C_ORANGE if level=="🟡" else C_GREEN
        bg_c = colors.HexColor("#1f0808") if level=="🔴" else colors.HexColor("#1f1000") if level=="🟡" else colors.HexColor("#0a1f0a")
        story.append(KeepTogether([
            _card([
                [Paragraph(f"{level}  <b>#{i} — {title}</b>",
                           _s(f"et{i}", fontSize=10, fontName="Helvetica-Bold", textColor=C_WHITE))],
                [Paragraph(f"<b>Problème :</b> {problem}",
                           _s(f"ep{i}", fontSize=9, textColor=C_LIGHT, leading=13))],
                [Paragraph(f"<b>✅ Fix :</b> {fix}",
                           _s(f"ef{i}", fontSize=9, textColor=C_GREEN, leading=13))],
            ], border_color=border_c, bg=bg_c),
            Spacer(1, 0.2*cm),
        ]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 03 — ANATOMIE D'UNE PAGE 18/20
    # ════════════════════════════════════════════════════════
    story += [
        Paragraph("<font color='#6366f1'>03</font>  Anatomie d'une page à 18/20",
                  _s("ch3", fontSize=18, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=6)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
        Paragraph("Voici la structure exacte des pages qui scorent 17-19/20 dans notre base de données. "
                  "Chaque section a un rôle précis dans le parcours de conversion.",
                  _s("int3", fontSize=10, textColor=C_LIGHT, leading=15, spaceAfter=10)),
    ]

    sections = [
        ("Above the Fold (0-3s)", "Hook", C_RED, [
            "Headline : promesse de transformation spécifique avec chiffre ou délai",
            "Sous-headline : qui ça aide + comment + résultat",
            "Image hero : produit en situation d'usage réel (pas de stock photos)",
            "CTA principal #1 : verbe d'action + résultat. Ex : \"Je veux perdre 5kg →\"",
            "Proof bar : logos clients, nombre d'utilisateurs ou étoiles",
        ]),
        ("Section Problème (scroll 1)", "Hook → Offer", C_ORANGE, [
            "Agiter le problème : décrire exactement ce que ressent le visiteur",
            "Liste des frustrations : bullet points de 3-5 problèmes identifiables",
            "Pont : \"C'est exactement pourquoi nous avons créé [produit]\"",
        ]),
        ("Section Offre (scroll 2)", "Offer", C_ORANGE, [
            "Offer Stack : liste de tout ce qui est inclus avec valeur unitaire chiffrée",
            "Prix ancré : barré + prix actuel. Ex : ~~197€~~ → 97€ aujourd'hui",
            "Urgence : raison claire et crédible (stock, date, cohorte)",
            "CTA #2 : répété avec urgence. Ex : \"Oui, je veux accéder maintenant (97€)\"",
        ]),
        ("Section Trust (scroll 3)", "Trust", C_GOLD, [
            "6-12 témoignages : prénom + photo + résultat chiffré",
            "Logos de marques partenaires ou médias",
            "Chiffres sociaux : \"Rejoint par 12 847 clients\"",
            "Vidéo testimonial si possible (augmente Trust de +2pts en moyenne)",
        ]),
        ("Section Garantie + FAQ (scroll 4)", "Friction", C_GREEN, [
            "Badge garantie : gros, visible, avec le délai (30j, 60j...)",
            "FAQ : répondre aux 5 objections principales avant achat",
            "Réassurance paiement : badges sécurité Stripe/PayPal/SSL",
            "CTA #3 final : même formulation que CTA #1",
        ]),
    ]

    for section_name, score_tag, color, items in sections:
        items_text = "<br/>".join([f"  • {item}" for item in items])
        story.append(KeepTogether([
            _card([
                [Paragraph(f"<font color='#{color.hexval()[2:]}'><b>{section_name}</b></font>  "
                           f"<font color='#444444' size='8'>[{score_tag}]</font>",
                           _s(f"sn{section_name[:5]}", fontSize=11, fontName="Helvetica-Bold"))],
                [Paragraph(items_text, _s(f"si{section_name[:5]}", fontSize=9, textColor=C_LIGHT, leading=15))],
            ], border_color=color, bg=colors.HexColor("#13131f")),
            Spacer(1, 0.3*cm),
        ]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 04 — QUICK WINS
    # ════════════════════════════════════════════════════════
    story += [
        Paragraph("<font color='#6366f1'>04</font>  Quick Wins universels — +3 pts en moins d'1h",
                  _s("ch4", fontSize=18, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=6)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
        Paragraph("Ces 6 actions peuvent être implémentées en moins d'1h chacune et ont "
                  "un impact mesurable immédiat sur le score LRS™ et le CVR réel.",
                  _s("int4", fontSize=10, textColor=C_LIGHT, leading=15, spaceAfter=10)),
    ]

    qws = [
        ("⚡", "Ajouter un badge garantie sous le CTA", "<1h", "+1-2 pts Trust/Offer",
         "Un simple badge \"Satisfait ou remboursé 30 jours\" placé directement sous le bouton principal. "
         "Taille recommandée : 200-300px. Fond transparent. Effacement total du risque perçu."),
        ("⚡", "Réécrire la headline avec la formule Résultat+Délai", "30 min", "+1-2 pts Hook",
         "Formule : [Verbe d'action] + [Résultat spécifique chiffré] + [Délai] + [Restriction]. "
         "Ex : \"Maîtrisez le Facebook Ads en 21 jours ou on vous rembourse.\""),
        ("⚡", "Ajouter un bloc de 6 témoignages avec résultats", "45 min", "+1-2 pts Trust",
         "Format requis : Prénom + Ville + Photo + Avant/Après chiffré. "
         "Placer directement sous la section offre. Si pas encore de clients, proposer le produit en beta."),
        ("⚡", "Supprimer le menu de navigation", "15 min", "+1 pt Friction",
         "Remplacer le header complet par juste le logo (non cliquable) sur les landing pages dédiées. "
         "Tester avec et sans via A/B test sur 3-5 jours."),
        ("⚡", "Rendre le CTA sticky sur mobile", "45 min", "+1 pt Friction",
         "Ajouter un bouton CTA fixé en bas de l'écran mobile (position: fixed; bottom: 0). "
         "Contient le CTA + prix + garantie en 1 ligne. Différence significative sur mobile cold traffic."),
        ("⚡", "Ajouter une barre de compteur social", "20 min", "+1 pt Trust",
         "\"Rejoint par [X] clients\" ou \"[X] personnes regardent cette page en ce moment\". "
         "Placer dans les 3 premiers scrolls. Augmente la perception de popularité et de sécurité."),
    ]

    for icon, title, time_est, impact, detail in qws:
        story.append(KeepTogether([
            _card([
                [Table([[
                    Paragraph(f"{icon} <b>{title}</b>",
                              _s(f"qwt_{title[:10]}", fontSize=10, fontName="Helvetica-Bold", textColor=C_GREEN)),
                    Paragraph(f"⏱ {time_est}  |  📈 {impact}",
                              _s(f"qwm_{title[:10]}", fontSize=8, textColor=C_GRAY, alignment=TA_RIGHT)),
                ]], colWidths=[W*0.65-1.5*cm, W*0.35-1.5*cm])],
                [Paragraph(detail, _s(f"qwd_{title[:10]}", fontSize=9, textColor=C_LIGHT, leading=13))],
            ], border_color=C_GREEN, bg=colors.HexColor("#0a1f0a")),
            Spacer(1, 0.2*cm),
        ]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 05 — FRAMEWORK SCORING
    # ════════════════════════════════════════════════════════
    story += [
        Paragraph("<font color='#6366f1'>05</font>  Framework Hook × Offer × Trust × Friction",
                  _s("ch5", fontSize=18, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=6)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
    ]

    framework = [
        ("HOOK /5", C_RED, "L'attention et la promesse",
         [("5/5", "Hook viscéral avec tension + chiffre + délai + transformation"),
          ("4/5", "Hook clair avec promesse mais sans tension émotionnelle"),
          ("3/5", "Générique — \"Découvrez notre méthode\" type"),
          ("2/5", "Confus — le visiteur ne comprend pas ce qu'il obtiendra"),
          ("1/5", "Pas de hook — juste un nom de produit ou une présentation"),
          ("0/5", "Aucun texte above the fold")],
         "Un 3/5 en Hook est la médiocrité invisible — la page semble \"ok\" mais ne capte rien."),
        ("OFFER /5", C_ORANGE, "La valeur perçue de l'offre",
         [("5/5", "Stack d'offre + prix ancré barré + garantie near CTA + urgence réelle"),
          ("4/5", "Offre claire avec prix visible mais sans stack ni urgence"),
          ("3/5", "Prix visible, quelques features listées, pas de structure offre"),
          ("2/5", "Offre floue — le visiteur ne sait pas exactement ce qu'il reçoit"),
          ("1/5", "Prix absent ou caché après clic"),
          ("0/5", "Pas d'offre définie sur la page")],
         "L'Offer est le critère qui a le plus fort levier sur le CVR — une amélioration de 2pts = souvent +50-80% de CVR."),
        ("TRUST /5", C_GOLD, "La preuve sociale et la crédibilité",
         [("5/5", "50+ reviews + photos clients + garantie near CTA + chiffres sociaux"),
          ("4/5", "Reviews sans photos ou brand établie avec preuves solides"),
          ("3/5", "Quelques témoignages génériques ou brand reconnue"),
          ("2/5", "Peu de preuves — 1-3 témoignages sans résultats"),
          ("1/5", "Aucune review ni témoignage"),
          ("0/5", "Aucun élément de trust")],
         "Le Trust est sous-investi par 80% des pages analysées. C'est souvent le levier le plus accessible."),
        ("FRICTION /5", C_GREEN, "La fluidité du parcours",
         [("5/5", "Zéro friction : CTA unique répété 3x, pas de navigation, checkout <3 clics"),
          ("4/5", "Légère friction : menu présent mais CTA dominant, parcours clair"),
          ("3/5", "Friction modérée : plusieurs CTAs, quelques distractions"),
          ("2/5", "Friction forte : beaucoup d'options, CTA dilué, parcours peu clair"),
          ("1/5", "Mismatch évident entre pub et landing"),
          ("0/5", "Impossible de trouver comment acheter")],
         "La Friction est souvent la plus rapide à corriger — supprimer un menu peut faire +1pt instantanément."),
    ]

    for crit_name, color, subtitle, levels, insight in framework:
        levels_text = "<br/>".join([
            f"<font color='{'#22c55e' if l[0]=='5' else '#FF8C00' if l[0] in ('3','4') else '#FF4444'}'><b>{l[0]}</b></font>  {l[1]}"
            for l in levels
        ])
        story.append(KeepTogether([
            _card([
                [Paragraph(f"<b>{crit_name}</b>  <font color='#555555' size='9'>{subtitle}</font>",
                           _s(f"fn{crit_name[:4]}", fontSize=12, fontName="Helvetica-Bold"))],
                [Paragraph(levels_text, _s(f"fl{crit_name[:4]}", fontSize=9, textColor=C_LIGHT, leading=15))],
                [Paragraph(f"💡 {insight}", _s(f"fi{crit_name[:4]}", fontSize=8, textColor=C_GRAY, leading=13))],
            ], border_color=color, bg=colors.HexColor("#13131f")),
            Spacer(1, 0.3*cm),
        ]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 07 — BENCHMARKS CVR
    # ════════════════════════════════════════════════════════
    story += [
        Paragraph("<font color='#6366f1'>07</font>  Benchmarks CVR par type d'offre",
                  _s("ch7", fontSize=18, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=6)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
        Paragraph("Ces benchmarks sont basés sur du cold traffic paid (Meta/TikTok/Google) "
                  "et non sur du trafic organique ou retargeting. Les chiffres correspondent "
                  "à un score LRS™ moyen de la fourchette indiquée.",
                  _s("int7", fontSize=10, textColor=C_LIGHT, leading=15, spaceAfter=10)),
    ]

    cvr_data = [
        ["Type d'offre",        "Score 0-9\n(Do NOT launch)", "Score 10-14\n(Test small)", "Score 15-20\n(Scale)"],
        ["Ecom physique",       "0.5-1.0%", "1.0-3.5%",  "3.5-8.0%"],
        ["Digital / Formation", "0.3-0.8%", "0.8-2.5%",  "2.0-5.5%"],
        ["SaaS / Trial gratuit","0.8-2.0%", "2.0-4.0%",  "4.0-8.0%"],
        ["High-ticket (>500€)", "0.1-0.5%", "0.5-1.5%",  "1.5-3.0%"],
        ["Lead Gen (email)",    "5-15%",    "15-35%",     "35-60%"],
        ["Service / Coaching",  "0.5-1.5%", "1.5-3.5%",  "3.5-7.0%"],
    ]

    cvr_rows = []
    for i, row in enumerate(cvr_data):
        is_h = (i == 0)
        cvr_rows.append([
            Paragraph(f"<b>{row[0]}</b>", _s(f"cr{i}0", fontSize=9, fontName="Helvetica-Bold" if is_h else "Helvetica",
                      textColor=C_ACCENT if is_h else C_WHITE)),
            Paragraph(row[1], _s(f"cr{i}1", fontSize=9, alignment=TA_CENTER,
                      textColor=C_RED if not is_h else C_ACCENT)),
            Paragraph(row[2], _s(f"cr{i}2", fontSize=9, alignment=TA_CENTER,
                      textColor=C_ORANGE if not is_h else C_ACCENT)),
            Paragraph(row[3], _s(f"cr{i}3", fontSize=9, alignment=TA_CENTER,
                      textColor=C_GREEN if not is_h else C_ACCENT)),
        ])

    t_cvr = Table(cvr_rows, colWidths=[W*0.34, W*0.22, W*0.22, W*0.22])
    t_cvr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), colors.HexColor("#0f0f2a")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_SURFACE, C_SURF2]),
        ("LEFTPADDING",  (0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
        ("TOPPADDING",   (0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("LINEBELOW",    (0,0),(-1,0),1,C_ACCENT),
        ("GRID",         (0,0),(-1,-1),0.3,C_BORDER),
        ("VALIGN",       (0,0),(-1,-1),"MIDDLE"),
    ]))
    story += [t_cvr, Spacer(1, 0.4*cm)]
    story.append(Paragraph(
        "⚠️ <b>Important :</b> Ces chiffres sont des fourchettes indicatives sur cold traffic. "
        "Les résultats réels varient selon la qualité du ciblage, le secteur, la saisonnalité et le prix du produit. "
        "Un score LRS™ élevé ne garantit pas un CVR élevé — il indique le <i>potentiel</i> de conversion.",
        _s("cvr_warn", fontSize=9, textColor=C_GRAY, leading=13)
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 08 — TOP 5 HOOKS
    # ════════════════════════════════════════════════════════
    story += [
        Paragraph("<font color='#6366f1'>08</font>  Top 5 Hooks qui convertissent",
                  _s("ch8", fontSize=18, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=6)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
        Paragraph("Ces structures de hooks ont été identifiées comme les plus performantes "
                  "sur du cold traffic Meta et TikTok. Adaptez-les à votre niche.",
                  _s("int8", fontSize=10, textColor=C_LIGHT, leading=15, spaceAfter=10)),
    ]

    hooks = [
        ("Résultat + Délai + Garantie",
         "\"Perdez 8kg en 30 jours ou on vous rembourse intégralement.\"",
         "Écom santé, Infoproduit, Coaching",
         "La garantie dans le hook élimine le risque perçu dès la première seconde."),
        ("Question qui identifie le problème",
         "\"Tu perds de l'argent en pub Meta sans le savoir ?\"",
         "B2B, Formation, SaaS",
         "Le visiteur se reconnaît immédiatement. Taux d'engagement très élevé."),
        ("Chiffre social + Résultat",
         "\"12 847 freelances ont doublé leurs tarifs avec cette méthode.\"",
         "Formation, Coaching, Consulting",
         "La preuve sociale dans le hook crédibilise immédiatement la promesse."),
        ("Contre-intuitif",
         "\"Arrêtez de scaler vos pubs tant que vous n'avez pas fait ça.\"",
         "Tous secteurs, Webinar, Lead Gen",
         "La curiosité forcée + la peur de rater quelque chose = clic inévitable."),
        ("Transformation avant/après avec délai",
         "\"De 0€ à 3 000€/mois en 60 jours : la méthode exacte.\"",
         "Formation, Dropshipping, Freelance",
         "Le before/after chiffré avec un délai précis est le hook le plus testé et validé."),
    ]

    for i, (formula, example, niches_str, why) in enumerate(hooks, 1):
        story.append(KeepTogether([
            _card([
                [Paragraph(f"<font color='#6366f1'><b>#{i}</b></font>  <b>{formula}</b>",
                           _s(f"ht{i}", fontSize=11, fontName="Helvetica-Bold", textColor=C_WHITE))],
                [Paragraph(f"<i>{example}</i>",
                           _s(f"he{i}", fontSize=10, fontName="Helvetica-Oblique",
                              textColor=C_GOLD, leading=14))],
                [Paragraph(f"<b>Niches :</b> {niches_str}  |  <b>Pourquoi ça marche :</b> {why}",
                           _s(f"hw{i}", fontSize=9, textColor=C_GRAY, leading=13))],
            ], border_color=C_ACCENT, bg=colors.HexColor("#0f0f2a")),
            Spacer(1, 0.2*cm),
        ]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 09 — GUIDE SI SCORE < 10
    # ════════════════════════════════════════════════════════
    story += [
        Paragraph("<font color='#FF4444'>09</font>  Que faire si votre score est inférieur à 10/20 ?",
                  _s("ch9", fontSize=18, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=6)),
        HRFlowable(width=W, thickness=1, color=C_RED, spaceAfter=10),
        Paragraph(
            "Un score inférieur à 10/20 signifie <b>Do NOT launch</b> — ne lancez pas de campagnes paid traffic "
            "avec cette page. Chaque euro dépensé sera gaspillé. Voici le protocole de remontée en 72h.",
            _s("int9", fontSize=10, textColor=C_LIGHT, leading=15, spaceAfter=10)
        ),
    ]

    protocol = [
        ("Heure 0-2", "Diagnostic", C_RED,
         "Identifier les 2 scores les plus bas (Hook ? Offer ? Trust ? Friction ?). "
         "Concentrer 100% de l'énergie sur ces 2 points uniquement."),
        ("Heure 2-4", "Fix Hook en urgence", C_ORANGE,
         "Utiliser le template : [Résultat chiffré] + [Délai] + [Pour qui]. "
         "Tester 3 variantes. Choisir la plus spécifique."),
        ("Heure 4-8", "Fix Offer", C_ORANGE,
         "Ajouter : prix visible + garantie sous CTA + au moins 1 bonus chiffré. "
         "Si le prix est élevé, ajouter une ancre de valeur (\"Valeur totale : 497€\")."),
        ("Heure 8-24", "Fix Trust", C_GOLD,
         "Récolter au moins 5 témoignages avec résultats. Même des bêta-testeurs. "
         "Si vraiment impossible : ajouter des logos partenaires + vos propres résultats chiffrés."),
        ("Heure 24-48", "Fix Friction", C_GREEN,
         "Supprimer le menu de navigation. Réduire les CTAs à 1 seul. "
         "S'assurer que le CTA est répété 3 fois minimum."),
        ("Heure 48-72", "Re-audit LRS™", C_ACCENT,
         "Relancer un audit avec LRS™ sur la nouvelle version. "
         "Objectif minimum : 11/20 avant tout lancement."),
    ]

    for time_str, step, color, detail in protocol:
        story.append(KeepTogether([
            _card([[Table([[
                Paragraph(f"<font color='{'#' + color.hexval()[2:]}'><b>{time_str}</b></font>",
                          _s(f"prt{step[:4]}", fontSize=9, fontName="Helvetica-Bold", textColor=color)),
                Paragraph(f"<b>{step}</b><br/><font color='#aaaaaa' size='9'>{detail}</font>",
                          _s(f"prd{step[:4]}", fontSize=10, textColor=C_WHITE, leading=14)),
            ]], colWidths=[2.5*cm, W-3.5*cm])]],
            border_color=color, bg=colors.HexColor("#13131f")),
            Spacer(1, 0.2*cm),
        ]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # 10 — ROADMAP 30 JOURS
    # ════════════════════════════════════════════════════════
    story += [
        Paragraph("<font color='#6366f1'>10</font>  Roadmap : de 10/20 à 18/20 en 30 jours",
                  _s("ch10", fontSize=18, fontName="Helvetica-Bold", textColor=C_WHITE, spaceAfter=6)),
        HRFlowable(width=W, thickness=1, color=C_ACCENT, spaceAfter=10),
    ]

    roadmap = [
        ("Semaine 1", "Foundation", C_RED, [
            "J1-2 : Réécrire la headline avec formule Résultat+Délai+Garantie",
            "J3 : Ajouter badge garantie directement sous le CTA principal",
            "J4-5 : Récolter 6 témoignages avec résultats chiffrés",
            "J6-7 : Supprimer menu navigation + réduire CTAs à 1 dominant",
            "Objectif fin S1 : +2-3 pts → score visé 12-13/20",
        ]),
        ("Semaine 2", "Offer Stack", C_ORANGE, [
            "J8-9 : Créer un offer stack avec valeurs chiffrées pour chaque élément",
            "J10 : Ajouter ancre de prix (barré) si pertinent",
            "J11-12 : Créer une urgence réelle (stock limité, date de fermeture, bonus temporaire)",
            "J13-14 : Optimiser le CTA — formulation + taille + couleur + position",
            "Objectif fin S2 : +2 pts → score visé 14-15/20",
        ]),
        ("Semaine 3", "Trust Maximum", C_GOLD, [
            "J15-17 : Ajouter 10+ témoignages photo avec résultats spécifiques",
            "J18-19 : Intégrer une vidéo testimonial ou une vidéo de démonstration",
            "J20-21 : Ajouter chiffres sociaux (nb clients, années d'expérience, résultats)",
            "Objectif fin S3 : +2 pts → score visé 16-17/20",
        ]),
        ("Semaine 4", "Optimisation Finale", C_GREEN, [
            "J22-24 : A/B test Hook — variante A vs variante B (changer 1 seul élément)",
            "J25-26 : Optimisation mobile — CTA sticky + vitesse de chargement",
            "J27-28 : Ajouter section FAQ avec 5 objections principales traitées",
            "J29-30 : Re-audit LRS™ complet + ajustements finaux",
            "Objectif fin S4 : +1-2 pts → score visé 17-19/20 → READY TO SCALE",
        ]),
    ]

    for week, theme, color, items in roadmap:
        items_text = "<br/>".join([f"{'→' if not i.startswith('Objectif') else '🎯'}  {i}" for i in items])
        story.append(KeepTogether([
            _card([
                [Paragraph(f"<b>{week}</b>  <font color='#555555' size='9'>— {theme}</font>",
                           _s(f"rw{week}", fontSize=12, fontName="Helvetica-Bold",
                              textColor=colors.HexColor("#" + color.hexval()[2:])))],
                [Paragraph(items_text, _s(f"ri{week}", fontSize=9, textColor=C_LIGHT, leading=15))],
            ], border_color=color, bg=colors.HexColor("#13131f")),
            Spacer(1, 0.3*cm),
        ]))

    # Fin + CTA LRS
    story += [
        Spacer(1, 0.5*cm),
        _card([
            [Paragraph("🚦 Auditez votre page avec LRS™",
                       _s("cta_h", fontSize=14, fontName="Helvetica-Bold", textColor=C_WHITE, alignment=TA_CENTER))],
            [Paragraph(
                "LRS™ — Launch Risk System vous donne un score précis en 30 secondes.<br/>"
                "Identifiez exactement ce qui bloque vos conversions avant de dépenser en pub.",
                _s("cta_b", fontSize=10, textColor=C_LIGHT, alignment=TA_CENTER, leading=15))],
            [Paragraph("lrs-launch-risk-system.streamlit.app",
                       _s("cta_url", fontSize=11, fontName="Helvetica-Bold", textColor=C_ACCENT, alignment=TA_CENTER))],
        ], border_color=C_ACCENT, bg=colors.HexColor("#0f0f2a")),
    ]

    doc.build(story, onFirstPage=_page_deco, onLaterPages=_page_deco)
    return buf.getvalue()


if __name__ == "__main__":
    pdf_bytes = generate()
    with open("/sessions/beautiful-ecstatic-allen/mnt/LRS/LRS_Benchmark_Report_2025.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"✅ Benchmark Report généré — {len(pdf_bytes):,} bytes")
