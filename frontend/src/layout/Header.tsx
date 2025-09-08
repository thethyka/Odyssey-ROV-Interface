import MissionStatusIndicator from "../components/MissionStatusIndicator";
export default function Header() {
    return (
        <header className="header h-36 flex flex-row justify-center items-center border-red-500 border-2">
            <section className="header-ba w-3/5 h-20 bg-surface flex flex-row items-center px-6">
                <MissionStatusIndicator />
                {/* <MasterAlarmIndicator/> */}
            </section>
        </header>
    );
}
