import useRovStore from "../../../store/rovStore";
import type {
    SetPropulsionStateCommand,
    DeployArmCommand,
    CollectSampleCommand,
    JettisonPackageCommand,
} from "../../../types";

import { CubeIcon, GaugeIcon, ScrewdriverIcon } from "@phosphor-icons/react";

import type { Icon } from "@phosphor-icons/react";

export default function SubsystemCard(props: { id: string }) {
    const rovState = useRovStore((state) => state.telemetry.rov_state);
    let name: string;
    let status: string;
    let icon: Icon;

    switch (props.id) {
        case "manipulator":
            status = rovState.manipulator_arm.status;
            name = "Manipulator Arm";
            icon = ScrewdriverIcon;
            break;
        case "propulsion":
            status = rovState.propulsion.status;
            name = "Propulsion";
            icon = GaugeIcon;
            break;
        case "science-package":
            status = rovState.science_package.status;
            name = "Science Package";
            icon = CubeIcon;
            break;
        default:
            return null;
    }

    return (
        <div className="cardContainer flex-1">
            <div className="internal">
                <div className="statusSection"></div>
                hei
                <div className="buttonSection"></div>
            </div>
        </div>
    );
}
