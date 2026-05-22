import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SeeWeeS Scenario Command Center",
  description: "Interactive dashboard prototype for SeeWeeS agentic disruption planning."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
