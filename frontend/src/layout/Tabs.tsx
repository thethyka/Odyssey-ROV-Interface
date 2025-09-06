import type { TabConfig } from "../types";

type TabsProps = {
  tabs: TabConfig[];
  activeTabId: string;
  setActiveTabId: (id: string) => void;
};

export default function Tabs({ tabs, activeTabId, setActiveTabId }: TabsProps) {
  return null;
}
