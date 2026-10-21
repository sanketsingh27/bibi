import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "App discovery · Bibi",
  description: "Local keyword discovery for the Apple App Store.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
