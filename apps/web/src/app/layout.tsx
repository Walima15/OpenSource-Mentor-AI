import type { Metadata } from "next";
import { Fraunces, Source_Sans_3 } from "next/font/google";

import { Nav } from "@/components/Nav";
import "./globals.css";

const serif = Fraunces({ subsets: ["latin"], variable: "--font-serif" });
const sans = Source_Sans_3({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "OSMA — Open Source Mentor",
  description: "A mentor for contributing to Bitcoin open-source projects.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${serif.variable} ${sans.variable} font-sans text-ink antialiased`}>
        <Nav />
        {children}
      </body>
    </html>
  );
}
