import { create } from "zustand";
import type { TelemetryMessage, RovStoreState } from "../types";

const initialState: TelemetryMessage = {
    timestamp: new Date().toISOString(),
    rov_state: {
        power: { charge_percent: 100.0, status: "discharging" },
        propulsion: { power_level_percent: 0.0, status: "inactive" },
        hull_integrity: { hull_pressure_kpa: 0, status: "nominal" },
        manipulator_arm: { status: "stowed", sample_collected: false },
        science_package: { status: "attached" },
        environment: { depth_meters: 0.0, water_temp_celsius: 18.0 },
    },
    mission_state: { status: "standby", operator_override: false },
    alert: { active: false, severity: null, message: null },
};

const useRovStore = create<RovStoreState>((set) => ({
    telemetry: initialState,
    updateTelemetry: (newTelemetry) => set({ telemetry: newTelemetry }),
    sendCommand: () => {
        console.log("No ws connected yet!");
    },
    setSendCommand: (sendCommandFn) =>
        set((state) => ({
            ...state,
            sendCommand: sendCommandFn,
        })),
}));

export default useRovStore;
