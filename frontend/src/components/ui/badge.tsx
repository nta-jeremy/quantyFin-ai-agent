import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center justify-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-mono font-bold uppercase tracking-[0.6px] w-fit whitespace-nowrap shrink-0 [&>svg:not([class*='size-'])]:size-3",
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
        review: "border-transparent bg-[var(--rose-tint)] text-[var(--rose-deep)]",
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

const labelMap = {
  live: 'LIVE',
  gap: 'GAP',
  review: 'REVIEW',
  build: 'BUILD',
  plan: 'PLAN',
};

const variantMap = {
  live: 'live',
  gap: 'gap',
  review: 'review',
  build: 'build',
  plan: 'plan',
} as const;

export interface StatusBadgeProps extends Omit<React.ComponentProps<"span">, 'color'> {
  status: 'live' | 'gap' | 'review' | 'build' | 'plan';
}

function StatusBadge({ status, className, children, ...props }: StatusBadgeProps) {
  const resolvedVariant = status in variantMap ? variantMap[status] : 'default';
  const resolvedLabel = labelMap[status as keyof typeof labelMap] || String(status).toUpperCase();

  return (
    <Badge
      role="status"
      aria-label={children ? undefined : resolvedLabel}
      variant={resolvedVariant}
      className={cn("font-mono font-bold tracking-[0.6px] uppercase", className)}
      {...props}
    >
      {children || resolvedLabel}
    </Badge>
  )
}

export { Badge, badgeVariants, StatusBadge }
