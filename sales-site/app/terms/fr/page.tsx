import type { Metadata } from "next";
import { LegalShell, LegalSection, LegalNotice } from "@/components/legal-shared";

export const metadata: Metadata = {
  title: "Conditions générales d'utilisation — LRS™",
  robots: { index: false, follow: false },
};

export default function TermsPageFr() {
  return (
    <LegalShell
      backHref="/vente/fr"
      backLabel="← Retour à LRS™"
      title="Conditions générales d'utilisation"
      updatedLabel="Dernière mise à jour : en attente de relecture finale avant mise en ligne"
    >
      <LegalNotice>
        <strong>Base de départ raisonnable, pas un avis juridique.</strong>{" "}
        Faites-la valider par un professionnel avant mise en ligne,
        notamment les clauses de responsabilité et de résiliation, et
        complétez l&apos;identité de l&apos;exploitant dans la Politique
        de confidentialité.
      </LegalNotice>

      <LegalSection heading="1. Objet">
        <p>
          LRS™ (« le Service ») est un outil d&apos;audit de landing
          pages et de publicités (hook, offre, confiance, friction) qui
          renvoie un verdict clair et des recommandations avant de
          dépenser de l&apos;argent en trafic payant.
        </p>
      </LegalSection>

      <LegalSection heading="2. Abonnement">
        <p>
          L&apos;accès au Service nécessite un abonnement payant,
          facturé mensuellement via Stripe. L&apos;abonnement se
          renouvelle automatiquement jusqu&apos;à résiliation. La
          résiliation prend effet à la fin de la période en cours ;
          aucun remboursement au prorata n&apos;est effectué sauf
          mention contraire. Le prix bêta, une fois verrouillé, reste
          verrouillé tant que l&apos;abonnement reste actif sans
          interruption.
        </p>
      </LegalSection>

      <LegalSection heading="3. Utilisation autorisée">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            Vous êtes responsable du contenu que vous soumettez au
            Service (URLs, textes publicitaires).
          </li>
          <li>
            Vous ne soumettez pas de contenu illégal, de contenu
            appartenant à un tiers sans autorisation, ni ne tentez de
            perturber ou contourner la sécurité du Service.
          </li>
          <li>
            Le compte est personnel — le partage d&apos;un accès payant
            avec des tiers non autorisés n&apos;est pas permis.
          </li>
        </ul>
      </LegalSection>

      <LegalSection heading="4. Nature du service — limitation de responsabilité">
        <p>
          Les scores et recommandations sont générés par un modèle
          d&apos;intelligence artificielle et fournis à titre indicatif.
          Ils ne constituent ni une garantie de performance
          publicitaire, ni un conseil professionnel (marketing,
          juridique ou autre). Vous restez seul responsable des
          décisions prises sur la base de ces recommandations.
        </p>
      </LegalSection>

      <LegalSection heading="5. Disponibilité">
        <p>
          Le Service est fourni « en l&apos;état ». Nous nous efforçons
          d&apos;assurer une disponibilité raisonnable mais ne
          garantissons pas un fonctionnement ininterrompu ou sans
          erreur.
        </p>
      </LegalSection>

      <LegalSection heading="6. Résiliation">
        <p>
          Vous pouvez résilier votre abonnement à tout moment. Nous
          pouvons suspendre ou résilier un accès en cas de violation
          manifeste de ces conditions.
        </p>
      </LegalSection>

      <LegalSection heading="7. Contact">
        <p>
          Pour toute question relative à ces conditions : [email de
          contact — à compléter].
        </p>
      </LegalSection>

      <LegalSection heading="Voir aussi">
        <p>
          Consultez également notre{" "}
          <a href="/privacy/fr" className="text-accent hover:underline">
            Politique de confidentialité
          </a>
          .
        </p>
      </LegalSection>
    </LegalShell>
  );
}
