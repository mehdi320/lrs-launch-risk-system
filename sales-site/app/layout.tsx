import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LRS™ — Launch Risk System",
  description:
    "Audit your landing page and your ad before you spend on paid traffic.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
