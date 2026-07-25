import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Smith IDE — Split-Attention Synchronised Agents",
  description: "Author, check, and run agent scripts with live structural feedback",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
