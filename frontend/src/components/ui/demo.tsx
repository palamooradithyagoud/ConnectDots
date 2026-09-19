"use client"

import NavigationMenu4 from "./navigation-menu-4"

export default function Demo() {
  return (
    <div className="w-full min-h-screen bg-background text-foreground">
      <NavigationMenu4 />
      <main className="container mx-auto px-4 py-16 text-center">
        <h1 className="text-3xl font-extrabold tracking-tight">Navigation Menu 4 Demo</h1>
        <p className="mt-4 text-muted-foreground">
          Hover over the navigation links or view on mobile to interact with the responsive navigation menu.
        </p>
      </main>
    </div>
  )
}
