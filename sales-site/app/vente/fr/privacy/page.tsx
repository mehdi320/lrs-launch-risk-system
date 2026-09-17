import type { Metadata } from "next";
import { LegalLayout, LegalSection } from "@/components/legal-shared";

export const metadata: Metadata = {
  title: "Politique de confidentialité — LRS™",
  robots: { index: false, follow: false },
};

export default function PrivacyFrPage() {
  return (
    <LegalLayout
      backHref="/vente/fr"
      backLabel="← Retour à LRS™"
      title="Politique de confidentialité"
      updatedLabel="Dernière mise à jour : à compléter avant publication"
      noticeLabel="Modèle à personnaliser."
      notice="Ce texte décrit fidèlement les données que LRS™ traite techniquement
        (voir le code du projet), mais ce n'est pas un avis juridique.
        Faites-le relire par un professionnel avant mise en ligne, en
        particulier si vous visez des utilisateurs dans l'UE (RGPD) — nom
        légal de l'exploitant, base légale de traitement, délégué à la
        protection des données le cas échéant, etc."
    >
      <LegalSection heading="Qui exploite LRS™">
        <p>
          [Nom / raison sociale de l&apos;exploitant], [adresse ou pays
          d&apos;établissement], [email de contact].
        </p>
      </LegalSection>

      <LegalSection heading="Données que nous traitons">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong>Contenu que vous soumettez</strong> : URL de landing page
            et/ou texte publicitaire que vous collez pour lancer un audit —
            transmis à un modèle d&apos;IA (OpenAI ou Anthropic selon
            configuration) pour générer le score et les recommandations.
          </li>
          <li>
            <strong>Adresse email</strong> : utilisée pour l&apos;authentification
            (lien de connexion à usage unique) et, si vous l&apos;activez,
            l&apos;envoi du rapport d&apos;audit ou d&apos;alertes de suivi.
          </li>
          <li>
            <strong>Données d&apos;abonnement</strong> : statut
            d&apos;abonnement, identifiant client et identifiant
            d&apos;abonnement Stripe. Nous ne voyons ni ne stockons jamais
            votre numéro de carte bancaire — le paiement est intégralement
            géré par Stripe.
          </li>
          <li>
            <strong>Historique d&apos;audits</strong> : scores et résultats
            des audits que vous lancez, conservés pour vous permettre de
            suivre votre progression.
          </li>
          <li>
            <strong>Cookie de session</strong> : un seul cookie, strictement
            nécessaire pour rester connecté — aucun cookie publicitaire ou de
            mesure d&apos;audience par défaut.
          </li>
        </ul>
      </LegalSection>

      <LegalSection heading="Destinataires / sous-traitants">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong>OpenAI et/ou Anthropic</strong> — génèrent l&apos;analyse
            à partir du contenu que vous soumettez.
          </li>
          <li>
            <strong>Stripe</strong> — traite le paiement de l&apos;abonnement.
          </li>
          <li>
            <strong>Notre prestataire d&apos;envoi d&apos;email (SMTP)</strong> —
            achemine les emails transactionnels (lien de connexion, rapports).
          </li>
          <li>
            Le cas échéant, si vous activez des intégrations optionnelles
            (Slack, Google Sheets, Notion, Meta/TikTok Ads) : ces services
            reçoivent uniquement les données que vous choisissez d&apos;y
            envoyer.
          </li>
        </ul>
      </LegalSection>

      <LegalSection heading="Durée de conservation">
        <p>
          Vos données sont conservées tant que votre compte est actif. Vous
          pouvez demander leur suppression à tout moment à [email de
          contact].
        </p>
      </LegalSection>

      <LegalSection heading="Vos droits">
        <p>
          Selon votre juridiction (RGPD pour les résidents de l&apos;UE
          notamment), vous disposez d&apos;un droit d&apos;accès, de
          rectification, de suppression et de portabilité de vos données.
          Contactez [email de contact] pour l&apos;exercer.
        </p>
      </LegalSection>

      <LegalSection heading="Sécurité">
        <p>
          Les mots de passe et jetons de connexion sont traités avec des
          mécanismes de comparaison à temps constant, les liens de connexion
          sont à usage unique et expirent après 15 minutes, et l&apos;accès à
          l&apos;application est protégé par abonnement.
        </p>
      </LegalSection>
    </LegalLayout>
  );
}
