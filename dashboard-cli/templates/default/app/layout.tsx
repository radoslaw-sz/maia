import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "../components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Test Report Dashboard",
  description: "Visualize test reports",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} flex gradient-bg text-text-primary`}>
        <Sidebar />
        <main className="flex-grow p-5 overflow-y-auto">{children}</main>
      </body>
    </html>
  );
}