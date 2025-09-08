import MissionStatusIndicator from "../components/MissionStatusIndicator";
import MasterAlertIndicator from "../components/MasterAlertIndicator";

export default function Header() {
    return (
        <header className="header h-36 flex flex-row justify-center items-center">
            <section className="header-ba w-3/5 h-20 bg-surface flex flex-row justify-between items-center px-6 rounded-lg border border-border gap-x-4">
                <MissionStatusIndicator />
                <MasterAlertIndicator />
            </section>
        </header>
    );
}
