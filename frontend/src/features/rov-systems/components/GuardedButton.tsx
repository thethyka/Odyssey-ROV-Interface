import React, { useState, useEffect, useRef } from "react";
import Button from "./Button";
import type { ComponentProps } from "react";

// Get the props type from the Button component itself
type ButtonProps = ComponentProps<typeof Button>;

interface GuardedButtonProps extends ButtonProps {
    confirmationText?: string;
    confirmationTimeout?: number;
}

export default function GuardedButton({
    onClick,
    children,
    confirmationText = "Confirm?",
    confirmationTimeout = 3000, // 3 seconds
    variant,
    ...props
}: GuardedButtonProps) {
    const [isArmed, setIsArmed] = useState(false);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    // Effect to automatically disarm the button after the timeout
    useEffect(() => {
        if (isArmed) {
            timerRef.current = setTimeout(() => {
                setIsArmed(false);
            }, confirmationTimeout);
        }

        // Cleanup function to clear the timer if the component unmounts
        // or if the button is clicked again.
        return () => {
            if (timerRef.current) {
                clearTimeout(timerRef.current);
            }
        };
    }, [isArmed, confirmationTimeout]);

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
        if (isArmed) {
            // If armed, execute the original onClick function
            if (onClick) {
                onClick(e);
            }
            setIsArmed(false);
        } else {
            // If not armed, arm the button
            setIsArmed(true);
        }
    };

    return (
        <Button
            onClick={handleClick}
            variant={isArmed ? "destructive" : variant}
            {...props}
        >
            {isArmed ? confirmationText : children}
        </Button>
    );
}
