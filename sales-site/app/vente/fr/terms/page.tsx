import type { Metadata } from "next";
import { LegalLayout, LegalSection } from "@/components/legal-shared";

export const metadata: Metadata = {
  title: "Conditions générales d'utilisation — LRS™",
  robots: { index: false, follow: false },
};

export default function TermsFrPage() {
  return (
    <LegalLayout
      backHref="/vente/fr"
      backLabel="← Retour à LRS™"
      title="Conditions générales d'utilisation"
      updatedLabel="Dernière mise à jour : à compléter avant publication"
      noticeLabel="Modèle à personnaliser."
      notice="Base de départ raisonnable, pas un avis juridique — faites-la
        valider par un professionnel avant mise en ligne, notamment les
        clauses de responsabilité et de résiliation."
    >
      <LegalSection heading="1. Objet">
        <p>
          LRS™ (« le Service ») est un outil d&apos;audit de landing pages et
          de publicités qui évalue une page ou un texte publicitaire (hook,
          offre, confiance, friction) et propose des recommandations, avant
          le lancement d&apos;une campagne payante.
        </p>
      </LegalSection>

      <LegalSection heading="2. Abonnement">
        <p>
          L&apos;accès au Service nécessite un abonnement payant, facturé
          mensuellement via Stripe. L&apos;abonnement se renouvelle
          automatiquement jusqu&apos;à résiliation. La résiliation prend
          effet à la fin de la période en cours ; aucun remboursement au
          prorata n&apos;est effectué sauf mention contraire.
        </p>
      </LegalSection>

      <LegalSection heading="3. Utilisation autorisée">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            Vous êtes responsable du contenu que vous soumettez au Service
            (URLs, textes publicitaires).
          </li>
          <li>
            Vous ne soumettez pas de contenu illégal, de contenu appartenant
            à un tiers sans autorisation, ni ne tentez de perturber ou
            contourner la sécurité du Service.
          </li>
          <li>
            Le compte est personnel — le partage d&apos;un accès payant avec
            des tiers non autorisés n&apos;est pas permis.
          </li>
        </ul>
      </LegalSection>

      <LegalSection heading="4. Nature du service — limitation de responsabilité">
        <p>
          Les scores et recommandations générés par LRS™ sont produits par un
          modèle d&apos;intelligence artificielle et fournis à titre
          indicatif. Ils ne constituent ni une garantie de performance
          publicitaire, ni un conseil professionnel (marketing, juridique ou
          autre). Vous restez seul responsable des décisions prises sur la
          base de ces recommandations.
        </p>
      </LegalSection>

      <LegalSection heading="5. Disponibilité">
        <p>
          Le Service est fourni « en l&apos;état ». Nous nous efforçons
          d&apos;assurer une disponibilité raisonnable mais ne garantissons
          pas un fonctionnement ininterrompu ou sans erreur.
        </p>
      </LegalSection>

      <LegalSection heading="6. Résiliation">
        <p>
          Vous pouvez résilier votre abonnement à tout moment. Nous pouvons
          suspendre ou résilier un accès en cas de violation manifeste de ces
          conditions.
        </p>
      </LegalSection>

      <LegalSection heading="7. Contact">
        <p>Pour toute question relative à ces conditions : [email de contact].</p>
      </LegalSection>
    </LegalLayout>
  );
}
