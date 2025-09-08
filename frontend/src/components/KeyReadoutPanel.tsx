import useRovStore from "../store/rovStore";

export default function KeyReadoutPanel() {
    const telemetry = useRovStore((state) => state.telemetry);

    const { depth_meters } =
        telemetry.rov_state.environment;
    const { charge_percent } = telemetry.rov_state.power;
    const { hull_pressure_kpa } = telemetry.rov_state.hull_integrity;

    return (
        <div className="flex flex-col gap-y-4">
            <div>
                <p className="font-sans font-medium text-xs text-text-secondary uppercase tracking-wider">
                    Depth (m)
                </p>
                <p className="font-mono text-base text-text-primary">
                    {depth_meters.toFixed(1)}
                </p>
            </div>

            <div>
                <p className="font-sans font-medium text-xs text-text-secondary uppercase tracking-wider">
                    Battery (%)
                </p>
                <p className="font-mono text-base text-text-primary">
                    {charge_percent.toFixed(1)}
                </p>
            </div>

            <div>
                <p className="font-sans font-medium text-xs text-text-secondary uppercase tracking-wider">
                    Hull Pressure (kPa)
                </p>
                <p className="font-mono text-base text-text-primary">
                    {hull_pressure_kpa}
                </p>
            </div>
        </div>
    );
}
