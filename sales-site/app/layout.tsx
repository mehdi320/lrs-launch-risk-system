import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LRS™ — Launch Risk System",
  description:
    "Auditez votre landing page et votre publicité avant de dépenser en pub.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
