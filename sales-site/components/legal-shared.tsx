// Mise en page partagée par les quatre pages légales (privacy/terms ×
// en/fr). Reprend les tokens visuels du sales-site (fond #f5f5f7, texte
// #1d1d1f, accent #007aff) plutôt que le CSS inline du gabarit
// pilot_static/{privacy,terms}.html, pour rester cohérent avec le reste
// du site — mais le contenu reste la même logique : décrire fidèlement
// les données réellement traitées par CE site (pas un copier-coller
// générique).

export function LegalShell({
  backHref,
  backLabel,
  title,
  updatedLabel,
  children,
}: {
  backHref: string;
  backLabel: string;
  title: string;
  updatedLabel: string;
  children: React.ReactNode;
}) {
  return (
    <main className="min-h-screen bg-[#f5f5f7] px-6 py-16 sm:py-24">
      <div className="mx-auto max-w-2xl">
        <a
          href={backHref}
          className="text-sm font-semibold text-accent hover:underline"
        >
          {backLabel}
        </a>
        <h1 className="mt-5 text-3xl font-extrabold tracking-tight text-[#1d1d1f]">
          {title}
        </h1>
        <p className="mt-1 text-sm text-[#86868b]">{updatedLabel}</p>

        <div className="mt-8 space-y-7 rounded-3xl bg-white p-8 shadow-[0_2px_20px_rgba(0,0,0,0.05)] sm:p-10">
          {children}
        </div>
      </div>
    </main>
  );
}

export function LegalSection({
  heading,
  children,
}: {
  heading: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h2 className="text-base font-bold text-[#1d1d1f]">{heading}</h2>
      <div className="mt-2 space-y-3 text-sm leading-relaxed text-[#4b4b50]">
        {children}
      </div>
    </section>
  );
}

// Bandeau d'avertissement — seul point du texte qui n'est pas un fait
// technique vérifiable dans le code : l'identité légale de l'exploitant
// (raison sociale, SIRET/pays, email de contact) reste à compléter par
// Baki avant mise en ligne réelle, et un avis juridique RGPD reste
// recommandé puisque le site cible des visiteurs francophones/UE.
export function LegalNotice({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-[#ff9500]/30 bg-[#ff9500]/10 p-4 text-xs leading-relaxed text-[#1d1d1f]">
      {children}
    </div>
  );
}
