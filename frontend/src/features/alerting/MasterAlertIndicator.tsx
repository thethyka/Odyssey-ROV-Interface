import useRovStore from "../../store/rovStore";

export default function MasterAlertIndicator() {
    const alert = useRovStore((state) => state.telemetry.alert);

    const severityBorderMap: { [key: string]: string } = {
        INFO: "border-info",
        WARNING: "border-warning animate-flash",
        CRITICAL: "border-critical animate-flash",
    };

    const borderClass = alert.severity
        ? severityBorderMap[alert.severity]
        : "border-border";

    return (
        <div
            className={`rounded-lg bg-component border ${borderClass} px-3 py-2 flex items-center gap-x-3 transition-colors duration-300 min-h-[44px]`}
        >
            <p className="font-sans font-medium text-xs uppercase tracking-wider text-text-secondary">
                {alert.severity || "IDLE"}
            </p>

            {alert.message && (
                <p className="font-mono text-sm text-text-primary whitespace-normal break-words max-w-[450px]">
                    {alert.message}
                </p>
            )}
        </div>
    );
}
