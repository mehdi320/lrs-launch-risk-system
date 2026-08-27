# LRS — Alertes et rapports par email (SMTP)
#
# Extrait de app.py (send_audit_email, send_score_drop_alert,
# send_monitoring_digest, _get_smtp_config) pour être réutilisé par
# pilot_server.py. Chaque fonction accepte un `smtp_config` optionnel
# (host, port, user, password) ; à défaut elle lit SMTP_HOST/PORT/USER/
# PASSWORD dans l'environnement. app.py passe son propre _get_smtp_config()
# (qui lit aussi st.secrets sur Streamlit Cloud) pour garder ce comportement
# spécifique sans le dupliquer ici.

import datetime
import os
import smtplib
from email import encoders as email_encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

APP_VERSION = "3.5"


def get_smtp_config():
    return (
        os.getenv("SMTP_HOST", ""),
        int(os.getenv("SMTP_PORT", 587)),
        os.getenv("SMTP_USER", ""),
        os.getenv("SMTP_PASSWORD", ""),
    )


def send_audit_email(result, meta, to_email, pdf_bytes=None, smtp_config=None):
    """Envoie le résumé de l'audit par email. Configure SMTP_HOST/PORT/USER/PASSWORD dans .env."""
    host, port, user, password = smtp_config or get_smtp_config()
    if not host or not user:
        raise ValueError(
            "SMTP non configuré. Ajoutez SMTP_HOST/PORT/USER/PASSWORD dans .env"
        )

    c = result.get("_c", {})
    score = c.get("score", 0)
    decision = c.get("decision", "")
    url = meta.get("url", meta.get("offer_type", ""))
    ts = meta.get("timestamp", "")
    mode_m = meta.get("mode", "")

    score_color = "var(--danger)" if score <= 9 else "var(--warning)" if score <= 14 else "var(--success)"

    fp = result.get("fix_plan", {})
    top = fp.get("top_priority_action", {})
    qws = fp.get("quick_wins", [])[:3]

    qws_html = "".join(
        f"<li style='margin:4px 0;color:#555'>{qw.get('what', '')}</li>"
        for qw in qws
    )

    html_body = f"""
<!DOCTYPE html>
<html><body style='font-family:Inter,-apple-system,sans-serif;background:#f4f4f8;padding:24px'>
<div style='max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;
            box-shadow:0 2px 12px rgba(0,0,0,0.08)'>

  <div style='background:linear-gradient(135deg,var(--accent),#4f46e5);padding:24px 28px'>
    <div style='color:#fff;font-size:1.3rem;font-weight:800'>🚦 LRS™ — Résultat d'Audit</div>
    <div style='color:rgba(255,255,255,0.7);font-size:0.85rem;margin-top:4px'>{ts} · {mode_m}</div>
  </div>

  <div style='padding:24px 28px'>
    <div style='font-size:0.85rem;color:#888;margin-bottom:4px'>URL / Offre</div>
    <div style='font-size:0.95rem;color:#1a1a2e;margin-bottom:20px'>{url}</div>

    <div style='background:#f8f8fc;border-radius:10px;padding:20px;text-align:center;margin-bottom:20px'>
      <div style='color:#888;font-size:0.75rem;text-transform:uppercase;letter-spacing:1px'>Score LRS</div>
      <div style='color:{score_color};font-size:3.5rem;font-weight:900;line-height:1'>{score}</div>
      <div style='color:#aaa;font-size:0.9rem'>/20</div>
      <div style='color:{score_color};font-size:1.1rem;font-weight:700;margin-top:8px'>{decision}</div>
    </div>

    {"<div style='margin-bottom:20px'><div style='font-weight:700;color:#1a1a2e;margin-bottom:8px'>🎯 Action Prioritaire</div><div style='background:#fff0f0;border-left:3px solid var(--danger);border-radius:6px;padding:12px 16px;color:#333'>" + top.get("what", "") + "</div></div>" if top and top.get("what") else ""}

    {"<div><div style='font-weight:700;color:#1a1a2e;margin-bottom:8px'>⚡ Quick Wins</div><ul style='padding-left:18px;margin:0'>" + qws_html + "</ul></div>" if qws_html else ""}
  </div>

  <div style='background:#f4f4f8;padding:14px 28px;text-align:center'>
    <span style='color:#aaa;font-size:0.78rem'>LRS™ — Launch Risk System V{APP_VERSION}</span>
  </div>
</div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚦 LRS Audit — Score {score}/20 — {decision} — {str(url)[:40]}"
    msg["From"] = user
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    if pdf_bytes:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_bytes)
        email_encoders.encode_base64(part)
        safe_url = (url or "audit").replace("https://", "").replace("http://", "").replace("/", "_")[:40]
        fname_pdf = f"LRS_{ts.replace('/', '').replace(':', '').replace(' ', '_')}_{safe_url}.pdf"
        part.add_header("Content-Disposition", f"attachment; filename={fname_pdf}")
        msg.attach(part)

    with smtplib.SMTP(host, port) as server:
        server.ehlo()
        server.starttls()
        server.login(user, password)
        server.sendmail(user, to_email, msg.as_string())


def send_score_drop_alert(entry, prev_score, to_email, smtp_config=None):
    """Envoie une alerte immédiate quand un score baisse de plus de 2 points."""
    host, port, user, password = smtp_config or get_smtp_config()
    if not host or not user or not to_email:
        return False

    url_v = str(entry.get("url", "") or entry.get("offer_type", ""))[:80]
    sc = entry.get("score", 0)
    delta = sc - prev_score
    sc_col = "var(--danger)" if sc <= 9 else "var(--warning)" if sc <= 14 else "var(--success)"
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    html_body = f"""
<!DOCTYPE html>
<html><body style='font-family:Inter,-apple-system,sans-serif;background:#f4f4f8;padding:24px'>
<div style='max-width:580px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;
            box-shadow:0 2px 12px rgba(0,0,0,0.08)'>
  <div style='background:#1a0a0a;border-top:4px solid var(--danger);padding:20px 24px'>
    <div style='color:var(--danger);font-size:1.1rem;font-weight:800'>⚠️ Alerte chute de score</div>
    <div style='color:#aaa;font-size:0.82rem;margin-top:4px'>{now_str}</div>
  </div>
  <div style='padding:24px 28px'>
    <div style='font-size:0.85rem;color:#888;margin-bottom:4px'>Page</div>
    <div style='font-size:0.95rem;color:#1a1a2e;font-weight:600;margin-bottom:20px'>{url_v}</div>
    <div style='display:flex;gap:16px;margin-bottom:20px'>
      <div style='flex:1;background:#f8f8fc;border-radius:8px;padding:16px;text-align:center'>
        <div style='color:#888;font-size:0.72rem;text-transform:uppercase'>Score précédent</div>
        <div style='color:#888;font-size:2rem;font-weight:800'>{prev_score}/20</div>
      </div>
      <div style='flex:1;background:#fff0f0;border-radius:8px;padding:16px;text-align:center;border:1px solid #fecaca'>
        <div style='color:var(--danger);font-size:0.72rem;text-transform:uppercase'>Score actuel</div>
        <div style='color:{sc_col};font-size:2rem;font-weight:800'>{sc}/20</div>
      </div>
      <div style='flex:1;background:#fff0f0;border-radius:8px;padding:16px;text-align:center;border:1px solid #fecaca'>
        <div style='color:var(--danger);font-size:0.72rem;text-transform:uppercase'>Delta</div>
        <div style='color:var(--danger);font-size:2rem;font-weight:800'>▼ {abs(delta)}</div>
      </div>
    </div>
    <div style='background:#fff0f0;border-left:4px solid var(--danger);border-radius:6px;padding:12px 16px'>
      <strong style='color:var(--danger)'>Action recommandée</strong>
      <div style='color:#555;font-size:0.85rem;margin-top:4px'>
        Connectez-vous à LRS™ pour voir le plan d'action complet et lancer un re-audit.
      </div>
    </div>
  </div>
</div>
</body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚠️ LRS™ Alerte — Score chute de {abs(delta)} pts · {url_v[:40]}"
        msg["From"] = user
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to_email, msg.as_string())
        return True
    except Exception:
        return False


def send_monitoring_digest(monitored_entries, to_email, smtp_config=None):
    """Envoie un digest des pages surveillées avec scores actuels. Appelé après un run planifié."""
    host, port, user, password = smtp_config or get_smtp_config()
    if not host or not user or not to_email:
        return False

    now_str = datetime.datetime.now().strftime("%d/%m/%Y")

    rows_html = ""
    for entry in monitored_entries:
        url_v = str(entry.get("url", "") or entry.get("offer_type", ""))[:60]
        # entry["score"] peut être explicitement None (audit planifié jamais exécuté) —
        # .get("score", 0) ne s'applique pas dans ce cas car la clé existe déjà.
        sc = entry.get("score")
        sc = sc if sc is not None else 0
        dec = entry.get("decision", "")
        ts = entry.get("timestamp", "")
        prev_sc = entry.get("prev_score")
        sc_color = "var(--danger)" if sc <= 9 else "var(--warning)" if sc <= 14 else "var(--success)"
        delta_html = ""
        if prev_sc is not None:
            delta = sc - prev_sc
            delta_color = "var(--success)" if delta > 0 else "var(--danger)" if delta < 0 else "#888"
            delta_arrow = "▲" if delta > 0 else "▼" if delta < 0 else "="
            delta_html = f"<span style='color:{delta_color};margin-left:8px;font-size:0.8rem'>{delta_arrow} {abs(delta)} pts</span>"
        rows_html += f"""
        <tr>
          <td style='padding:10px 12px;border-bottom:1px solid #eee;color:#333;font-size:0.85rem'>{url_v}</td>
          <td style='padding:10px 12px;border-bottom:1px solid #eee;text-align:center'>
            <span style='color:{sc_color};font-weight:800;font-size:1.1rem'>{sc}/20</span>{delta_html}
          </td>
          <td style='padding:10px 12px;border-bottom:1px solid #eee;color:#555;font-size:0.82rem'>{dec}</td>
          <td style='padding:10px 12px;border-bottom:1px solid #eee;color:#999;font-size:0.78rem'>{ts}</td>
        </tr>"""

    danger_count = sum(1 for e in monitored_entries if (e.get("score") if e.get("score") is not None else 20) <= 9)
    alert_banner = ""
    if danger_count > 0:
        alert_banner = f"""
        <div style='background:#fff0f0;border-left:4px solid var(--danger);border-radius:6px;
                    padding:12px 16px;margin-bottom:20px'>
          <strong style='color:var(--danger)'>⚠️ {danger_count} page(s) en danger</strong>
          <div style='color:#555;font-size:0.85rem;margin-top:4px'>Score ≤ 9/20 — action requise immédiatement.</div>
        </div>"""

    html_body = f"""
<!DOCTYPE html>
<html><body style='font-family:Inter,-apple-system,sans-serif;background:#f4f4f8;padding:24px'>
<div style='max-width:640px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;
            box-shadow:0 2px 12px rgba(0,0,0,0.08)'>
  <div style='background:linear-gradient(135deg,var(--accent),#4f46e5);padding:24px 28px'>
    <div style='color:#fff;font-size:1.2rem;font-weight:800'>📊 LRS™ — Digest de Monitoring</div>
    <div style='color:rgba(255,255,255,0.7);font-size:0.85rem;margin-top:4px'>{now_str} · {len(monitored_entries)} pages surveillées</div>
  </div>
  <div style='padding:24px 28px'>
    {alert_banner}
    <table style='width:100%;border-collapse:collapse'>
      <thead>
        <tr style='background:#f8f8fc'>
          <th style='padding:8px 12px;text-align:left;font-size:0.75rem;color:#888;text-transform:uppercase;letter-spacing:0.5px'>Page</th>
          <th style='padding:8px 12px;text-align:center;font-size:0.75rem;color:#888;text-transform:uppercase;letter-spacing:0.5px'>Score</th>
          <th style='padding:8px 12px;text-align:left;font-size:0.75rem;color:#888;text-transform:uppercase;letter-spacing:0.5px'>Décision</th>
          <th style='padding:8px 12px;text-align:left;font-size:0.75rem;color:#888;text-transform:uppercase;letter-spacing:0.5px'>Dernier audit</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    <div style='margin-top:20px;padding-top:16px;border-top:1px solid #eee;
                color:#aaa;font-size:0.78rem;text-align:center'>
      Généré par LRS™ V{APP_VERSION} — Launch Risk System
    </div>
  </div>
</div>
</body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"LRS™ Digest — {len(monitored_entries)} pages · {now_str}"
        msg["From"] = user
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to_email, msg.as_string())
        return True
    except Exception:
        return False


def send_magic_link_email(to_email, magic_link_url, smtp_config=None):
    """Envoie le lien de connexion à usage unique (15 min) pour accéder à LRS."""
    host, port, user, password = smtp_config or get_smtp_config()
    if not host or not user or not to_email:
        return False

    html_body = f"""
<!DOCTYPE html>
<html><body style='font-family:Inter,-apple-system,sans-serif;background:#f4f4f8;padding:24px'>
<div style='max-width:480px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;
            box-shadow:0 2px 12px rgba(0,0,0,0.08)'>
  <div style='background:linear-gradient(135deg,var(--accent),#4f46e5);padding:24px 28px'>
    <div style='color:#fff;font-size:1.2rem;font-weight:800'>🚦 LRS™ — Votre lien de connexion</div>
  </div>
  <div style='padding:24px 28px'>
    <p style='color:#333;font-size:0.95rem;line-height:1.6'>
      Cliquez sur le bouton ci-dessous pour accéder à LRS™. Ce lien est valable
      15 minutes et à usage unique.
    </p>
    <div style='text-align:center;margin:24px 0'>
      <a href='{magic_link_url}'
         style='display:inline-block;background:var(--accent);color:#fff;text-decoration:none;
                padding:12px 28px;border-radius:8px;font-weight:700;font-size:0.95rem'>
        Accéder à LRS →
      </a>
    </div>
    <p style='color:#999;font-size:0.78rem;line-height:1.5'>
      Si vous n'avez pas demandé ce lien, ignorez simplement cet email.
    </p>
  </div>
</div>
</body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🚦 Votre lien de connexion LRS™"
        msg["From"] = user
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to_email, msg.as_string())
        return True
    except Exception:
        return False
