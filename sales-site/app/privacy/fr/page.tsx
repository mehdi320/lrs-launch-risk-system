import type { Metadata } from "next";
import { LegalShell, LegalSection, LegalNotice } from "@/components/legal-shared";

export const metadata: Metadata = {
  title: "Politique de confidentialité — LRS™",
  robots: { index: false, follow: false },
};

export default function PrivacyPageFr() {
  return (
    <LegalShell
      backHref="/vente/fr"
      backLabel="← Retour à LRS™"
      title="Politique de confidentialité"
      updatedLabel="Dernière mise à jour : en attente de relecture finale avant mise en ligne"
    >
      <LegalNotice>
        <strong>Brouillon — identité de l&apos;exploitant à compléter.</strong>{" "}
        Ce texte décrit fidèlement ce que fait réellement ce site précis
        (la page de vente d&apos;où vous venez, pas l&apos;application LRS
        elle-même) avec les données, d&apos;après son code source. Ce
        n&apos;est pas un avis juridique. Avant une mise en ligne réelle,
        complétez la raison sociale et l&apos;email de contact ci-dessous,
        et faites-le relire par un professionnel si vous ciblez des
        visiteurs de l&apos;UE (RGPD).
      </LegalNotice>

      <LegalSection heading="Qui exploite ce site">
        <p>
          [Raison sociale / statut de l&apos;exploitant — à compléter],
          [adresse ou pays d&apos;établissement — à compléter], [email de
          contact — à compléter].
        </p>
      </LegalSection>

      <LegalSection heading="Ce que fait ce site, concrètement">
        <p>
          Cette page présente l&apos;offre LRS™ et permet de s&apos;abonner.
          Elle ne collecte aucun contenu d&apos;audit et ne crée aucun
          compte — cela se passe sur une application séparée une fois
          l&apos;abonnement souscrit. Il n&apos;y a ni formulaire de
          contact ni base de données côté serveur derrière cette page.
        </p>
      </LegalSection>

      <LegalSection heading="Données traitées par ce site">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong>Choix de consentement cookies</strong> : stocké
            uniquement dans le navigateur (localStorage), jamais transmis
            à un serveur.
          </li>
          <li>
            <strong>Cookies publicitaires / analytiques</strong> (Meta
            Pixel, Google Ads/Analytics) : chargés uniquement après
            acceptation explicite du bandeau. En cas de refus ou
            d&apos;absence de choix, aucun des deux scripts ne se charge
            et aucun cookie tiers n&apos;est déposé.
          </li>
          <li>
            <strong>Informations de paiement</strong> : au clic pour
            rejoindre la bêta, Stripe collecte directement votre email et
            vos informations de paiement — via une page Stripe hébergée
            ou un widget Stripe intégré. Nous ne voyons ni ne stockons
            jamais votre numéro de carte ; Stripe traite et conserve ces
            données selon sa propre politique de confidentialité.
          </li>
        </ul>
      </LegalSection>

      <LegalSection heading="Destinataires de ces données">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong>Meta</strong> — uniquement si vous acceptez les
            cookies et que le Meta Pixel est actif.
          </li>
          <li>
            <strong>Google</strong> — uniquement si vous acceptez les
            cookies et que Google Ads/Analytics est actif.
          </li>
          <li>
            <strong>Stripe</strong> — traite le paiement de
            l&apos;abonnement.
          </li>
        </ul>
      </LegalSection>

      <LegalSection heading="Durée de conservation">
        <p>
          Votre choix cookies reste dans votre navigateur jusqu&apos;à
          suppression des données du site ou modification via le
          bandeau. Stripe conserve les données de paiement et de
          facturation selon sa propre politique. Ce site ne conserve
          aucune trace côté serveur de votre visite.
        </p>
      </LegalSection>

      <LegalSection heading="Vos droits">
        <p>
          Si vous résidez dans l&apos;UE (RGPD) ou dans une juridiction
          offrant des protections similaires, vous disposez d&apos;un
          droit d&apos;accès, de rectification, de suppression et de
          portabilité de vos données. Pour les données détenues par
          Stripe, vous pouvez aussi contacter Stripe directement. Pour
          exercer ces droits concernant ce site, contactez [email de
          contact — à compléter].
        </p>
      </LegalSection>

      <LegalSection heading="Voir aussi">
        <p>
          Consultez également nos{" "}
          <a href="/terms/fr" className="text-accent hover:underline">
            Conditions générales
          </a>
          .
        </p>
      </LegalSection>
    </LegalShell>
  );
}
