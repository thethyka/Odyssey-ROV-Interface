import useRovStore from "../store/rovStore";
import ScenarioSelector from "../features/MainContent/ScenarioSelector";
import ViewSwitcher from "../features/MainContent/ViewSwitcher";

export default function MainContent() {
    const missionStatus = useRovStore(
        (state) => state.telemetry.mission_state.status
    );

    const showSelector = missionStatus === "standby";

    return (
        <section className="main-content grow rounded-lg border border-border mb-4 flex flex-col">
            {showSelector ? <ScenarioSelector /> : <ViewSwitcher />}
        </section>
    );
}
