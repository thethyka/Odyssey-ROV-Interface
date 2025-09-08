import type { TabConfig } from "../../types";

type TabsProps = {
    tabs: TabConfig[];
    activeTabId: string;
    setActiveTabId: (id: string) => void;
};

export default function Tabs({ tabs, activeTabId, setActiveTabId }: TabsProps) {
    return (
        <div className="flex border-b border-border justify-center">
            {tabs.map((tab) => {
                const isActive = tab.id === activeTabId;
                return (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTabId(tab.id)}
                        className={`px-4 py-2 font-sans text-sm transition-colors ${
                            isActive
                                ? "text-text-primary border-b-2 border-info"
                                : "text-text-secondary hover:text-text-primary"
                        }`}
                    >
                        {tab.label}
                    </button>
                );
            })}
        </div>
    );
}
