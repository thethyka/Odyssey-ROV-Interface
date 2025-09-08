import KeyReadoutPanel from "../components/KeyReadoutPanel";
import LiveAlertFeed from "../components/LiveAlertFeed";

export default function LeftSidebar() {
    return (
        <section className="leftbar w-80 flex flex-col items-center py-4">
            <div className="w-[80%] h-full bg-surface rounded-lg border border-border flex flex-col p-4 gap-y-6 justify-between">
                <KeyReadoutPanel />
                <LiveAlertFeed />
            </div>
        </section>
    );
}
