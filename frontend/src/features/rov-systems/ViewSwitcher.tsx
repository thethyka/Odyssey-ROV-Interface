import { useState } from "react";
import useRovStore from "../../store/rovStore";
import Tabs from "./components/Tabs";
import SystemOverview from "./SystemOverview";
import SubsystemControls from "./SubsystemControls";
import type { TabConfig } from "../../types";

const TABS_CONFIG: TabConfig[] = [
    { id: "system", label: "System Overview", component: <SystemOverview /> },
    {
        id: "subsystem",
        label: "Subsystem Controls",
        component: <SubsystemControls />,
    },
];

export default function ViewSwitcher() {
    const missionStatus = useRovStore(
        (state) => state.telemetry.mission_state.status
    );
    const sendCommand = useRovStore((state) => state.sendCommand);

    const [activeTabId, setActiveTabId] = useState(TABS_CONFIG[0].id);
    const activeTab = TABS_CONFIG.find((tab) => tab.id === activeTabId);

    const missionEnded =
        missionStatus === "mission_success" ||
        missionStatus.startsWith("mission_failure");

    const resetToStandby = () => {
        sendCommand({ command: "RESET_SIMULATION" });
    };

    return (
        <div className="flex flex-col h-full">
            {!missionEnded ? (
                <>
                    <Tabs
                        tabs={TABS_CONFIG}
                        activeTabId={activeTabId}
                        setActiveTabId={setActiveTabId}
                    />
                    <div className="flex-1">{activeTab?.component}</div>
                </>
            ) : (
                <div className="flex flex-col items-center justify-center h-full gap-y-4">
                    <p className="font-sans text-text-secondary">
                        Mission over.
                    </p>
                    <button
                        onClick={resetToStandby}
                        className="px-4 py-2 rounded-lg border border-border text-text-primary hover:bg-surface transition"
                    >
                        Return to Scenario Selector
                    </button>
                </div>
            )}
        </div>
    );
}
