import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Legal RAG Workbench",
  description: "A polished frontend for inspecting a legal RAG agent.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
