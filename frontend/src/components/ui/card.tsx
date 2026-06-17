import * as React from "react"

import { cn } from "@/lib/utils"

export interface CardProps extends React.ComponentProps<"div"> {
  variant?: "default" | "dashboard";
}

function Card({ className, variant = "default", ...props }: CardProps) {
  return (
    <div
      data-slot="card"
      data-variant={variant}
      data-surface={variant === "dashboard" ? "app" : undefined}
      className={cn(
        "group/card bg-card text-card-foreground flex flex-col gap-6 rounded-xl border border-border shadow-sm",
        variant === "default" ? "py-6" : "p-6",
        className
      )}
      {...props}
    />
  )
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "flex flex-col gap-1.5 px-6 group-data-[variant=dashboard]/card:px-0",
        className
      )}
      {...props}
    />
  )
}

function CardTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-title"
      className={cn("font-brand font-bold leading-none", className)}
      {...props}
    />
  )
}

function CardDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props}
    />
  )
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-content"
      className={cn("px-6 group-data-[variant=dashboard]/card:px-0", className)}
      {...props}
    />
  )
}

function CardFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-footer"
      className={cn(
        "flex items-center px-6 group-data-[variant=dashboard]/card:px-0",
        className
      )}
      {...props}
    />
  )
}

export type DashboardCardProps = Omit<CardProps, "variant">;

function DashboardCard(props: DashboardCardProps) {
  return <Card variant="dashboard" {...props} />
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  DashboardCard,
}
