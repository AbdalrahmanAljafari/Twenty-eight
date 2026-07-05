import type { Metadata } from "next";

import { SiteHeader } from "@/components/layout/site-header";
import { QueryProvider } from "@/components/providers/query-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "Twenty-eight",
  description: "Virtual try-on flow",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <QueryProvider>
          <SiteHeader />
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}
