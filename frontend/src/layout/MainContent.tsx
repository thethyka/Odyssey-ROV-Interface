import { useState } from "react";
import SubsystemControls from "../features/SubsystemControls/SubsystemControls.tsx";
import SystemOverview from "../features/SystemOverview/SystemOverview.tsx";
import Tabs from "./Tabs.tsx";

const TABS_CONFIG = [
  {
    id: "system",
    label: "System Overview",
    component: <SystemOverview />,
  },
  {
    id: "subsystem",
    label: "Subsystem Controls",
    component: <SubsystemControls />,
  },
];

export default function MainContent() {
  const [activeTabId, setActiveTabId] = useState(TABS_CONFIG[0].id);

  const activeTab = TABS_CONFIG.find((tab) => tab.id === activeTabId);

  return (
    <section className="main-content grow border-red-500 border-2">
      <Tabs
        tabs={TABS_CONFIG}
        activeTabId={activeTabId}
        setActiveTabId={setActiveTabId}
      />

      <div className="tab-content mt-4">{activeTab!.component}</div>
    </section>
  );
}
