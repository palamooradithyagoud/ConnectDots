import Component from "@/components/ui/navigation-menu-4"

export const metadata = {
  title: "Navigation Menu 4 Demo",
}

export default function DemoPage() {
  return (
    <div className="w-full min-h-[calc(100vh-80px)] bg-background text-foreground">
      <Component />
      <div className="max-w-4xl mx-auto py-16 px-6 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold uppercase tracking-wider mb-6">
          Shadcn UI Component Demo
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
          Navigation Menu 4
        </h1>
        <p className="mt-4 text-base text-muted-foreground max-w-2xl mx-auto">
          Fully integrated with Shadcn UI, Radix primitives, Lucide icons, and Tailwind CSS.
          Test hover dropdowns, submenu descriptions, and responsive mobile drawer state.
        </p>
      </div>
    </div>
  )
}
