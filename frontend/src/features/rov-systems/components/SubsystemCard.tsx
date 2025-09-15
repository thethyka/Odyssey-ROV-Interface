import useRovStore from "../../../store/rovStore";
import type {
    SetPropulsionStateCommand,
    DeployArmCommand,
    CollectSampleCommand,
    JettisonPackageCommand,
} from "../../../types";

import { CubeIcon, GaugeIcon, ScrewdriverIcon } from "@phosphor-icons/react";
import type { Icon } from "@phosphor-icons/react";
import Button from "./Button"; // Make sure to import your Button component
import GuardedButton from "./GuardedButton";
export default function SubsystemCard(props: { id: string }) {
    // Get state and the command sender from the store
    const rovState = useRovStore((state) => state.telemetry.rov_state);
    const sendCommand = useRovStore((state) => state.sendCommand);

    let name: string;
    let status: string;
    let icon: Icon;
    let actionButtons: React.ReactNode = null; // Variable to hold our conditional JSX

    switch (props.id) {
        case "propulsion": {
            status = rovState.propulsion.status;
            name = "Propulsion";
            icon = GaugeIcon;

            const isEngaged = rovState.propulsion.status === "active";
            const statusSet = isEngaged ? "inactive" : "active";
            const command: SetPropulsionStateCommand = {
                command: "SET_PROPULSION_STATE",
                payload: { status: statusSet },
            };

            actionButtons = (
                <Button variant="outline" onClick={() => sendCommand(command)}>
                    {isEngaged ? "Disengage Propulsion" : "Engage Propulsion"}
                </Button>
            );
            break;
        }

        case "manipulator": {
            status = rovState.manipulator_arm.status;
            name = "Manipulator Arm";
            icon = ScrewdriverIcon;

            const deployCommand: DeployArmCommand = { command: "DEPLOY_ARM" };
            const collectCommand: CollectSampleCommand = {
                command: "COLLECT_SAMPLE",
            };

            actionButtons = (
                <div className="flex space-x-2">
                    <Button
                        variant="outline"
                        onClick={() => sendCommand(deployCommand)}
                    >
                        Deploy Arm
                    </Button>
                    <Button
                        variant="outline"
                        onClick={() => sendCommand(collectCommand)}
                        disabled={
                            rovState.manipulator_arm.status !== "deployed"
                        }
                    >
                        Collect Sample
                    </Button>
                </div>
            );
            break;
        }

        case "science-package": {
            status = rovState.science_package.status;
            name = "Science Package";
            icon = CubeIcon;

            const command: JettisonPackageCommand = {
                command: "JETTISON_PACKAGE",
            };

            // 2. Use GuardedButton instead of Button
            actionButtons = (
                <GuardedButton
                    confirmationText="Confirm Jettison"
                    onClick={() => sendCommand(command)}
                    disabled={rovState.science_package.status === "jettisoned"}
                >
                    Jettison Package
                </GuardedButton>
            );
            break;
        }

        default:
            return null;
    }

    // The Icon component needs to be rendered dynamically
    const IconComponent = icon;

    return (
        <div className="cardContainer flex-1 bg-surface rounded-lg border border-border flex flex-col p-4 justify-between h-40">
            <div className="flex flex-col items-center h-20">
                <div className="flex items-center space-x-2">
                    <IconComponent size={20} className="text-text-secondary" />
                    <div className="font-mono text-text-primary">{name}</div>
                </div>
                <div className="font-mono text-text-secondary capitalize pt-4">
                    {status}
                </div>
            </div>
            <div className="flex-grow" />{" "}
            {/* This pushes the buttons to the bottom */}
            <div className="flex justify-center items-center pt-2">
                {actionButtons}
            </div>
        </div>
    );
}
