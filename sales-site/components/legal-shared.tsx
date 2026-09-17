// Mise en page partagée par les 4 pages légales (privacy/terms × en/fr).
// Même palette/typo que le reste de sales-site/ (voir vente-shared.tsx) —
// volontairement distincte du fond "glass" du pilote (pilot_static/) pour
// coller au style plus sobre déjà utilisé sur la page de vente elle-même.

export function LegalLayout({
  backHref,
  backLabel,
  title,
  updatedLabel,
  noticeLabel,
  notice,
  children,
}: {
  backHref: string;
  backLabel: string;
  title: string;
  updatedLabel: string;
  noticeLabel: string;
  notice: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <main className="min-h-screen bg-[#f5f5f7] px-6 py-16 sm:py-20">
      <div className="mx-auto max-w-2xl">
        <a
          href={backHref}
          className="text-sm font-semibold text-accent no-underline"
        >
          {backLabel}
        </a>
        <h1 className="mt-5 text-3xl font-extrabold tracking-tight text-[#1d1d1f]">
          {title}
        </h1>
        <p className="mt-1.5 text-sm text-[#86868b]">{updatedLabel}</p>

        <div className="mt-8 rounded-2xl bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)] sm:p-10">
          <div className="mb-8 rounded-xl border border-[#ff9500]/25 bg-[#ff9500]/10 px-4 py-3.5 text-sm leading-relaxed text-[#1d1d1f]">
            <strong>{noticeLabel}</strong> {notice}
          </div>
          <div className="legal-prose">{children}</div>
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
    <section className="mt-7 first:mt-0">
      <h2 className="text-base font-bold text-[#1d1d1f]">{heading}</h2>
      <div className="mt-2 space-y-2.5 text-[14.5px] leading-relaxed text-[#4b4b50]">
        {children}
      </div>
    </section>
  );
}
