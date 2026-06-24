import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenSource Mentor AI",
  description:
    "Your AI mentor for contributing to open-source: discover issues, understand repos, write code, and open pull requests.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
