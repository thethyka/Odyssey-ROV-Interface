import useRovStore from "../../store/rovStore";
import type { StartSimulationCommand } from "../../types";

export default function ScenarioSelector() {
  const sendCommand = useRovStore((state) => state.sendCommand);

  const startScenario = (scenario: "nominal" | "pressure_anomaly" | "power_fault") => {
    const command: StartSimulationCommand = {
      command: "START_SIMULATION",
      payload: { scenario },
    };
    sendCommand(command);
  };

  return (
    <div className="flex flex-col items-center justify-center h-full gap-y-6 bg-component rounded-lg border border-border p-8">
      <h2 className="font-sans text-lg font-semibold text-text-primary">
        Select a Simulation Scenario
      </h2>
      <div className="flex flex-col gap-y-3 w-60">
        <button
          onClick={() => startScenario("nominal")}
          className="px-4 py-2 rounded-lg border border-border text-text-primary hover:bg-surface transition"
        >
          Nominal Mission
        </button>
        <button
          onClick={() => startScenario("pressure_anomaly")}
          className="px-4 py-2 rounded-lg border border-border text-text-primary hover:bg-surface transition"
        >
          Pressure Anomaly
        </button>
        <button
          onClick={() => startScenario("power_fault")}
          className="px-4 py-2 rounded-lg border border-border text-text-primary hover:bg-surface transition"
        >
          Power Fault
        </button>
      </div>
    </div>
  );
}