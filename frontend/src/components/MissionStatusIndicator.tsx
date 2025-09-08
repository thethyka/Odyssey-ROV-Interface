import useRovStore from "../store/rovStore";

export default function MissionStatusIndicator() {
    const missionStatus = useRovStore(
        (state) => state.telemetry.mission_state.status
    );

    const statusColorMap: { [key: string]: string } = {
        mission_success: "border-nominal",
        mission_failure_hull_breach: "border-critical",
        mission_failure_lost_signal: "border-critical",
    };

    const colorClass = statusColorMap[missionStatus] || "";
    const formattedStatus = missionStatus.replace(/_/g, " ").toUpperCase();

    return (
        <div
            className={`rounded-lg bg-component border border-border px-3 py-2 flex items-center gap-x-4 transition-colors duration-300 ${colorClass}`}
        >
            <p className="font-sans font-medium text-xs text-text-secondary uppercase tracking-wider">
                Mission Status
            </p>

            <p className="font-mono text-base text-text-primary">
                {formattedStatus}
            </p>
        </div>
    );
}
