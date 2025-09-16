import MissionStatusIndicator from "../features/dashboard/MissionStatusIndicator";
import MasterAlertIndicator from "../features/alerting/MasterAlertIndicator";
import useRovStore from "../store/rovStore";

export default function Header() {
    const missionState = useRovStore(
        (state) => state.telemetry.mission_state.status
    );
    const renderSlug = ["returning", "mission_success"].includes(missionState);

    return (
        <>
            <header className="header h-36 flex flex-row justify-center items-center">
                <section className="header-ba w-3/5 h-20 bg-surface flex flex-row justify-between items-center px-6 rounded-lg border border-border gap-x-4">
                    <MissionStatusIndicator />
                    <MasterAlertIndicator />
                </section>
            </header>

            {renderSlug ? (
                <div className="fixed top-15 right-15">
                    <img
                        src="/slug.png"
                        alt="Slug logo"
                        className="h-12 w-auto"
                    />
                </div>
            ) : null}
        </>
    );
}
