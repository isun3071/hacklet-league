import type { Metadata } from "next";
import "./globals.css";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";

export const metadata: Metadata = {
  // One descriptor for the whole site. If this changes, change it here and nowhere else —
  // the description reuses the same string rather than inventing a second one.
  title: "HackLet League: a rapid app building league with automated stress testing",
  description: "a rapid app building league with automated stress testing",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
