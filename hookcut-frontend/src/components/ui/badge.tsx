import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))] focus:ring-offset-2 focus:ring-offset-[hsl(var(--background))]",
  {
    variants: {
      variant: {
        default:
          "bg-violet-500/20 text-violet-300 border border-violet-500/30",
        secondary:
          "bg-white/[0.04] text-white/60 border border-white/[0.08] backdrop-blur-xl",
        destructive:
          "bg-red-500/20 text-red-300 border border-red-500/30",
        outline:
          "bg-transparent text-white/60 border border-white/[0.1]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
