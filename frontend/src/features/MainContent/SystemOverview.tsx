// src/components/SystemOverview.tsx

import { useEffect, useMemo } from "react";
import ReactFlow, {
    ReactFlowProvider,
    Background,
    Controls,
    useNodesState,
    useEdgesState,
} from "reactflow";
import type { Node, Edge } from "reactflow";
import "reactflow/dist/style.css";

import useRovStore from "../../store/rovStore";
import SystemNode from "../../components/SystemNode";
import type { SystemNodeData } from "../../components/SystemNode";
import {
    BatteryChargingVerticalIcon,
    GaugeIcon,
    HardHatIcon,
    ScrewdriverIcon,
    CubeIcon,
    GearIcon,
} from "@phosphor-icons/react";

// Define initial positions for a clean layout
const initialNodes: Node<SystemNodeData>[] = [
    {
        id: "power",
        position: { x: 0, y: 150 },
        type: "systemNode",
        data: { label: "...", icon: GearIcon },
    },
    {
        id: "main-bus",
        position: { x: 250, y: 150 },
        type: "systemNode",
        data: { label: "...", icon: GearIcon },
    },
    {
        id: "propulsion",
        position: { x: 500, y: 0 },
        type: "systemNode",
        data: { label: "...", icon: GearIcon },
    },
    {
        id: "hull",
        position: { x: 500, y: 100 },
        type: "systemNode",
        data: { label: "...", icon: GearIcon },
    },
    {
        id: "manipulator",
        position: { x: 500, y: 200 },
        type: "systemNode",
        data: { label: "...", icon: GearIcon },
    },
    {
        id: "science-package",
        position: { x: 500, y: 300 },
        type: "systemNode",
        data: { label: "...", icon: GearIcon },
    },
];

const initialEdges: Edge[] = [
    { id: "power-bus", source: "power", target: "main-bus" },
    { id: "bus-propulsion", source: "main-bus", target: "propulsion" },
    { id: "bus-hull", source: "main-bus", target: "hull" },
    { id: "bus-manipulator", source: "main-bus", target: "manipulator" },
    { id: "bus-science", source: "main-bus", target: "science-package" },
];

// Map status to edge colors from your style guide
const statusEdgeColors: Record<string, string> = {
    nominal: "#34D399",
    warning: "#FBBF24",
    critical: "#F87171",
    fault: "#F87171",
    default: "#374151",
};

// Component that contains the actual React Flow logic
const FlowDiagram = () => {
    const telemetry = useRovStore((state) => state.telemetry);
    const { rov_state } = telemetry;

    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    // We must tell React Flow about our custom node type
    const nodeTypes = useMemo(() => ({ systemNode: SystemNode }), []);

    useEffect(() => {
        const updatedNodes = initialNodes.map((node) => {
            let data: SystemNodeData = { label: "Unknown", icon: GearIcon };
            switch (node.id) {
                case "power":
                    data = {
                        label: "Power System",
                        icon: BatteryChargingVerticalIcon,
                        // FIX #1: Translate backend status ('discharging'/'fault') to a valid NodeStatus.
                        status:
                            rov_state.power.status === "fault"
                                ? "critical"
                                : "nominal",
                        value: `${rov_state.power.charge_percent.toFixed(1)}%`,
                    };
                    break;
                case "main-bus":
                    data = {
                        label: "Main Bus",
                        icon: GearIcon,
                        // The main bus inherits its status from the power system because its operation depends on the power system's health.
                        status:
                            rov_state.power.status === "fault"
                                ? "critical"
                                : "nominal",
                        value: "Online",
                    };
                    break;
                case "propulsion":
                    data = {
                        label: "Propulsion",
                        icon: GaugeIcon,
                        status:
                            rov_state.propulsion.status === "active"
                                ? "nominal"
                                : "inactive",
                        value: `${rov_state.propulsion.power_level_percent.toFixed(
                            0
                        )}%`,
                    };
                    break;
                case "hull":
                    data = {
                        label: "Hull Integrity",
                        icon: HardHatIcon,
                        status: rov_state.hull_integrity.status,
                        value: `${(
                            rov_state.hull_integrity.hull_pressure_kpa / 100
                        ).toFixed(1)} bar`,
                    };
                    break;
                case "manipulator":
                    data = {
                        label: "Manipulator",
                        icon: ScrewdriverIcon,
                        status:
                            rov_state.manipulator_arm.status === "stowed"
                                ? "inactive"
                                : rov_state.manipulator_arm.sample_collected
                                ? "info"
                                : "nominal",
                        value: rov_state.manipulator_arm.sample_collected
                            ? "Sample Stored"
                            : rov_state.manipulator_arm.status,
                    };
                    break;
                case "science-package":
                    data = {
                        label: "Science Package",
                        icon: CubeIcon,
                        status:
                            rov_state.science_package.status === "attached"
                                ? "nominal"
                                : "critical",
                        value: rov_state.science_package.status,
                    };
                    break;
            }
            return { ...node, data };
        });

        const updatedEdges = initialEdges.map((edge) => {
            const sourceNode = updatedNodes.find((n) => n.id === edge.source);
            const sourceStatus = sourceNode?.data.status || "default";

            const isPropulsionEdge = edge.target === "propulsion";
            const isPropulsionActive = rov_state.propulsion.status === "active";

            return {
                ...edge,
                animated: isPropulsionEdge && isPropulsionActive,
                style: {
                    stroke:
                        statusEdgeColors[sourceStatus] ||
                        statusEdgeColors.default,
                    strokeWidth: 2,
                },
            };
        });

        // The "WOW" moment for the power fault scenario
        if (rov_state.science_package.status === "jettisoned") {
            setNodes(updatedNodes.filter((n) => n.id !== "science-package"));
            setEdges(
                updatedEdges.filter((e) => e.target !== "science-package")
            );
        } else {
            setNodes(updatedNodes);
            setEdges(updatedEdges);
        }
    }, [telemetry, setNodes, setEdges]); // End of useEffect

    return (
        <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView // This will zoom/pan to fit all nodes on screen
            className="bg-background"
        >
            <Background color="#374151" />
            <Controls />
        </ReactFlow>
    );
};

// Main component export, wrapped in the provider
const SystemOverview = () => {
    return (
        <div className="h-full w-full">
            <ReactFlowProvider>
                <FlowDiagram />
            </ReactFlowProvider>
        </div>
    );
};

export default SystemOverview;
