import SubsystemCard from "./components/SubsystemCard";

export default function SubsystemControls() {
    return (
        <div className="w-full h-full bg-background flex items-center px-5 gap-5">
            <SubsystemCard id="propulsion" />
            <SubsystemCard id="manipulator" />
            <SubsystemCard id="science-package" />
        </div>
    );
}
