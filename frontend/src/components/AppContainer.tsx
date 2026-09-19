"use client";

import React from "react";
import { usePathname } from "next/navigation";

export default function AppContainer({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isLandingPage = pathname === "/";

  if (isLandingPage) {
    return <main className="w-full">{children}</main>;
  }

  return (
    <main className="mx-auto max-w-[1600px] px-4 sm:px-6 lg:px-8 pb-12 pt-4">
      {children}
    </main>
  );
}
