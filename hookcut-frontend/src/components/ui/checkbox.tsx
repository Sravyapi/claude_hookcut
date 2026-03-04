"use client";

import * as React from "react";
import * as CheckboxPrimitive from "@radix-ui/react-checkbox";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

const Checkbox = React.forwardRef<
  React.ComponentRef<typeof CheckboxPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root>
>(({ className, ...props }, ref) => (
  <CheckboxPrimitive.Root
    ref={ref}
    className={cn(
      "peer h-[22px] w-[22px] shrink-0 rounded-md",
      "border-2 border-white/[0.15] bg-transparent",
      "transition-all duration-250 ease-[cubic-bezier(0.4,0,0.2,1)]",
      "hover:border-violet-500/50 hover:shadow-[0_0_8px_rgba(139,92,246,0.15)]",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/30 focus-visible:ring-offset-0",
      "disabled:cursor-not-allowed disabled:opacity-40",
      "data-[state=checked]:bg-gradient-to-br data-[state=checked]:from-violet-500 data-[state=checked]:to-violet-700",
      "data-[state=checked]:border-violet-500 data-[state=checked]:shadow-[0_0_12px_rgba(139,92,246,0.3)]",
      className
    )}
    {...props}
  >
    <CheckboxPrimitive.Indicator
      className={cn("flex items-center justify-center text-white")}
    >
      <Check className="h-3.5 w-3.5" strokeWidth={3} />
    </CheckboxPrimitive.Indicator>
  </CheckboxPrimitive.Root>
));
Checkbox.displayName = CheckboxPrimitive.Root.displayName;

export { Checkbox };
