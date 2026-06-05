import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * cn — merge class names with Tailwind-aware conflict resolution.
 * Standard shadcn/ui utility. Used by every component below.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
