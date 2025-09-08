// src/components/SystemNode.tsx

import type { FC } from "react";
import { Handle, Position } from "reactflow";
import type { Icon } from "@phosphor-icons/react";

// This type definition is correct. We will ensure the data we pass matches it.
type NodeStatus = "nominal" | "warning" | "critical" | "fault" | "inactive" | "info" | "success" | "default" |  null;

export interface SystemNodeData {
  label: string;
  icon: Icon;
  status?: NodeStatus;
  value?: string;
}

const statusBorderColors: Record<string, string> = {
    success: "border-nominal",
    warning: "border-warning",
    critical: "border-critical",
    fault: "border-critical",
    info: "border-info",
    inactive: "border-border",
    default: "border-border",
};

const SystemNode: FC<{ data: SystemNodeData }> = ({ data }) => {
    const { label, icon: IconComponent, status, value } = data;

    const borderColor = status
        ? statusBorderColors[status] || statusBorderColors.default
        : statusBorderColors.default;

    return (
        <div
            className={`
                w-48 h-24 bg-surface rounded-md border-2
                flex flex-col justify-between p-2
                transition-colors duration-500
                ${borderColor}
            `}
        >
            <Handle type="target" position={Position.Left} className="!bg-slate-500" />
            <Handle type="source" position={Position.Right} className="!bg-slate-500" />

            <div className="flex items-center space-x-2">
                <IconComponent size={20} className="text-text-secondary" />
                <span className="text-sm font-bold uppercase text-text-secondary tracking-wider">
                    {label}
                </span>
            </div>
            
            <div className="text-right">
                <span className="text-2xl font-mono text-text-primary">
                    {value || "---"}
                </span>
            </div>
        </div>
    );
};

export default SystemNode;