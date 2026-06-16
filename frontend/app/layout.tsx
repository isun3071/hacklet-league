import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HackLet League — competitive AI-assisted defensive coding",
  description:
    "Hackathon, but minutes instead of hours. 24 minutes, one sanctioned AI, then automated adversarial testing and live judging.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
