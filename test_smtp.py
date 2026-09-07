#!/usr/bin/env python3
"""Teste la config SMTP en isolation, avant de brancher le reste
(webhook Stripe, lien magique de connexion — voir STRIPE_SMTP_SETUP.md).

Usage :
    python3 test_smtp.py votre-email@exemple.com

Lit SMTP_HOST/PORT/USER/PASSWORD depuis .env (ou l'environnement), envoie
un vrai email de test à l'adresse donnée via la même fonction que celle
utilisée en production pour le lien magique de connexion
(email_alerts.send_magic_link_email), et donne un diagnostic clair en cas
d'échec plutôt que le simple True/False que renvoie la fonction en prod.
"""

import smtplib
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import email_alerts


def main():
    if len(sys.argv) != 2:
        print("Usage : python3 test_smtp.py votre-email@exemple.com")
        sys.exit(1)

    to_email = sys.argv[1]
    host, port, user, password = email_alerts.get_smtp_config()

    print("── Config SMTP lue depuis l'environnement ──")
    print(f"  SMTP_HOST     = {host or '(vide)'}")
    print(f"  SMTP_PORT     = {port}")
    print(f"  SMTP_USER     = {user or '(vide)'}")
    print(f"  SMTP_PASSWORD = {'*' * len(password) if password else '(vide)'}")
    print()

    if not host or not user or not password:
        print("❌ Config incomplète — vérifiez SMTP_HOST/USER/PASSWORD dans .env.")
        sys.exit(1)

    print(f"Connexion à {host}:{port}...")
    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            print("✅ Connexion + STARTTLS OK.")
            print("Authentification...")
            server.login(user, password)
            print("✅ Authentification OK.")
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentification refusée : {e}")
        print(
            "   → Gmail : utilisez un \"mot de passe d'application\" "
            "(https://myaccount.google.com/apppasswords), pas le mot de "
            "passe normal du compte."
        )
        print("   → Autre fournisseur : vérifiez SMTP_USER/SMTP_PASSWORD (souvent une clé API, pas un mot de passe).")
        sys.exit(1)
    except (smtplib.SMTPConnectError, TimeoutError, OSError) as e:
        print(f"❌ Connexion impossible à {host}:{port} : {e}")
        print("   → Vérifiez SMTP_HOST/SMTP_PORT et qu'un pare-feu ne bloque pas le port sortant.")
        sys.exit(1)

    print(f"\nEnvoi d'un email de test à {to_email}...")
    ok = email_alerts.send_magic_link_email(
        to_email,
        "https://exemple.test/?token=CECI_EST_UN_TEST",
        smtp_config=(host, port, user, password),
    )
    if ok:
        print(f"✅ Email envoyé à {to_email}. Vérifiez la boîte de réception (et les spams).")
        print("   Config SMTP validée — prête pour STRIPE_SMTP_SETUP.md.")
    else:
        print("❌ send_magic_link_email a échoué malgré une connexion/authentification OK — vérifiez les logs ci-dessus.")
        sys.exit(1)


if __name__ == "__main__":
    main()
