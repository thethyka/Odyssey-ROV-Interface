import React from "react";
import { cn } from "../../../lib/utils"; // Assuming you have a utility for merging class names

// Define the types for the component's props
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "outline" | "destructive" | "default";
}

export default function Button({
    variant = "default",
    className,
    children,
    ...props
}: ButtonProps) {
    // Define base styles for all buttons
    const baseStyles =
        "p-2 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background";

    // Define styles for each variant
    const variantStyles = {
        default: "bg-text-primary text-background hover:bg-text-primary/90",
        destructive:
            "bg-critical text-critical-foreground hover:bg-critical/90",
        outline:
            "border border-border bg-transparent hover:bg-component hover:text-text-primary",
    };

    return (
        <button
            className={cn(baseStyles, variantStyles[variant], className)}
            {...props}
        >
            {children}
        </button>
    );
}
