import useRovStore from "../../store/rovStore";

export default function LiveAlertFeed() {
    const alert = useRovStore((state) => state.telemetry.alert);
    const timestamp = useRovStore((state) => state.telemetry.timestamp);

    const severityColorMap: { [key: string]: string } = {
        INFO: "text-info",
        WARNING: "text-warning",
        CRITICAL: "text-critical",
    };

    const formattedTime = timestamp
        ? new Date(timestamp).toISOString().replace("T", " ").split(".")[0]
        : "";

    const colorClass = alert?.severity ? severityColorMap[alert.severity] : "";

    return (
        <div className="flex flex-col h-1/3 border-t border-border overflow-y-auto p-2">
            <p className="font-sans font-medium text-xs text-text-secondary uppercase tracking-wider mb-2">
                Alerts
            </p>

            {!alert?.active ? (
                <p className="font-mono text-sm text-text-secondary">
                    No active alerts
                </p>
            ) : (
                <div
                    className={`font-mono text-sm ${colorClass} whitespace-normal break-words`}
                >
                    <span className="text-text-secondary mr-2">
                        [{formattedTime}]
                    </span>
                    {alert.message}
                </div>
            )}
        </div>
    );
}
