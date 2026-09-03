// Composants et constantes partagés entre les deux versions linguistiques
// de la page de vente (app/vente/page.tsx = EN, app/vente/fr/page.tsx = FR).

// ---------------------------------------------------------------------------
// Champs éditables à la main pour la bêta — volontairement PAS de logique
// (pas de countdown, pas de décrément automatique). Si une place est prise,
// modifiez SPOTS_REMAINING vous-même avant de redéployer.
// ---------------------------------------------------------------------------
export const SPOTS_TOTAL = 17;
export const SPOTS_REMAINING = 17;
export const BETA_PRICE = "€50";
export const REGULAR_PRICE = "€100+";

export const STRIPE_LINK =
  process.env.NEXT_PUBLIC_STRIPE_LINK && process.env.NEXT_PUBLIC_STRIPE_LINK.length > 0
    ? process.env.NEXT_PUBLIC_STRIPE_LINK
    : "#";

export function PrimaryCta({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <a
      href={STRIPE_LINK}
      className={
        "inline-flex items-center justify-center rounded-full bg-accent px-8 py-4 text-base font-semibold text-white shadow-[0_8px_24px_rgba(0,122,255,0.35)] transition hover:bg-[#0066d6] active:scale-[0.98] " +
        className
      }
    >
      {children}
    </a>
  );
}

export function SectionEyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-3 text-xs font-bold uppercase tracking-[0.14em] text-accent">
      {children}
    </p>
  );
}

export function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-3xl font-extrabold tracking-tight text-[#1d1d1f] sm:text-4xl">
      {children}
    </h2>
  );
}

export function Prose({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-6 space-y-4 text-base leading-relaxed text-[#4b4b50] sm:text-lg">
      {children}
    </div>
  );
}

export function CheckList({ items }: { items: React.ReactNode[] }) {
  return (
    <ul className="mt-6 grid gap-3 sm:grid-cols-2">
      {items.map((item, i) => (
        <li
          key={i}
          className="flex items-start gap-2 rounded-2xl bg-white p-4 text-sm leading-relaxed text-[#1d1d1f] shadow-[0_2px_8px_rgba(0,0,0,0.04)]"
        >
          <span className="mt-0.5 text-accent">✓</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

// Bouton de bascule de langue, fixé en haut à droite de chaque version de
// la page (visible en permanence, y compris après scroll).
export function LangSwitch({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="fixed right-4 top-4 z-50 inline-flex items-center gap-1.5 rounded-full border border-black/10 bg-white/80 px-4 py-1.5 text-xs font-semibold text-[#1d1d1f] shadow-[0_2px_8px_rgba(0,0,0,0.06)] backdrop-blur transition hover:bg-white sm:right-6 sm:top-6"
    >
      🌐 {label}
    </a>
  );
}
