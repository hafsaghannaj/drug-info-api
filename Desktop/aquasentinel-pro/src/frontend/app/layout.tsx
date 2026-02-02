import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "AquaSentinel Pro",
  description: "Early warning platform for waterborne disease outbreak prediction",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
