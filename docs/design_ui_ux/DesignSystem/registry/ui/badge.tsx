import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Badge — shadcn/ui open-code component, quantyFin-branded via theme tokens.
 * Adds QuantyFin status variants (live / build / plan / gap) on top of the
 * standard default/secondary/destructive/outline set. Pill radius matches
 * the QuantyFin tag/chip language.
 */
const badgeVariants = cva(
  "inline-flex items-center justify-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-mono font-bold uppercase tracking-wider w-fit whitespace-nowrap shrink-0 [&>svg]:size-3",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground",
        outline: "text-foreground border-border",
        live: "border-transparent bg-[var(--mint-tint)] text-[var(--mint-deep)]",
        build: "border-transparent bg-[var(--iris-tint)] text-[var(--iris-deep)]",
        plan: "border-transparent bg-[var(--gold-tint)] text-[var(--gold-deep)]",
        gap: "border-transparent bg-[var(--gap-bg)] text-[var(--gap)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant,
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "span"
  return (
    <Comp
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
