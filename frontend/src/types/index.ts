// TypeScript type definitions
// Shared types for telemetry, alerts, etc.

import type { ReactNode } from "react";


export type TabConfig = {
    id: string;
    label: string;
    component: ReactNode;
  };