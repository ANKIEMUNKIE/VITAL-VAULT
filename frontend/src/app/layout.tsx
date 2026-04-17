import type { Metadata } from "next";
import { Fredoka, Nunito } from "next/font/google";
import "./globals.css";

const fredoka = Fredoka({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: '--font-headline' });
const nunito = Nunito({ subsets: ["latin"], weight: ["400", "500", "700", "900"], variable: '--font-body' });

export const metadata: Metadata = {
  title: "Vital Vault - Next.js Interactive",
  description: "Tactile Medical Dashboard ported to Next.js with Anime.js",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body className={`${fredoka.variable} ${nunito.variable} min-h-screen baseplate-pattern font-body text-black`} suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
