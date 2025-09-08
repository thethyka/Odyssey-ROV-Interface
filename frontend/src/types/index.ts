// TypeScript type definitions
// Shared types for telemetry, alerts, etc.

import type { ReactNode } from "react";

export type TabConfig = {
    id: string;
    label: string;
    component: ReactNode;
};

export type StartSimulationCommand = {
    command: "START_SIMULATION";
    payload: {
        scenario: "nominal" | "pressure_anomaly" | "power_fault";
    };
};

export type SetPropulsionStateCommand = {
    command: "SET_PROPULSION_STATE";
    payload: {
        status: "active" | "inactive";
    };
};

export type DeployArmCommand = {
    command: "DEPLOY_ARM";
};

export type CollectSampleCommand = {
    command: "COLLECT_SAMPLE";
};

export type JettisonPackageCommand = {
    command: "JETTISON_PACKAGE";
};

export type RovCommand =
    | StartSimulationCommand
    | SetPropulsionStateCommand
    | DeployArmCommand
    | CollectSampleCommand
    | JettisonPackageCommand;

export interface RovStoreState {
    telemetry: TelemetryMessage;
    updateTelemetry: (newTelemetry: TelemetryMessage) => void;
    sendCommand: (command: RovCommand) => void;
    setSendCommand: (sendCommandFn: (command: RovCommand) => void) => void;
}

export interface TelemetryMessage {
    timestamp: string;
    rov_state: RovState;
    mission_state: MissionState;
    alert: ActiveAlert;
}

export interface RovState {
    power: Power;
    propulsion: Propulsion;
    hull_integrity: HullIntegrity;
    manipulator_arm: ManipulatorArm;
    science_package: SciencePackage;
    environment: Environment;
}

export interface Power {
    charge_percent: number;
    status: "discharging" | "fault";
}

export interface Propulsion {
    power_level_percent: number;
    status: "active" | "inactive";
}

export interface HullIntegrity {
    hull_pressure_kpa: number;
    status: "nominal" | "warning" | "critical";
}

export interface ManipulatorArm {
    status: "stowed" | "deployed" | "gripping";
    sample_collected: boolean;
}

export interface SciencePackage {
    status: "attached" | "jettisoned";
}

export interface Environment {
    depth_meters: number;
    water_temp_celsius: number;
}

export interface MissionState {
    status:
        | "standby"
        | "en_route"
        | "searching"
        | "returning"
        | "mission_success"
        | "emergency_ascent"
        | "mission_failure_hull_breach"
        | "mission_failure_lost_signal";
    operator_override: boolean;
}

export interface ActiveAlert {
    active: boolean;
    severity: "INFO" | "WARNING" | "CRITICAL" | null;
    message: string | null;
}
