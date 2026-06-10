// For managing the WebSocket connection

import { useEffect } from "react";
import useRovStore from "../store/rovStore";
import type { RovCommand, TelemetryMessage } from "../types";

export const useTelemetry = () => {
    const updateTelemetry = useRovStore((state) => state.updateTelemetry);
    const setSendCommand = useRovStore((state) => state.setSendCommand);

    useEffect(() => {
        console.log("Attempting to connect...");

        const wsBaseUrl = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";
        const ws = new WebSocket(`${wsBaseUrl}/ws/telemetry`);

        ws.onopen = () => {
            console.log("Websocket connection established");

            setSendCommand((command: RovCommand) => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify(command));
                } else {
                    console.error(
                        "WebSocket is not open. Cannot send command."
                    );
                }
            });
        };

        ws.onmessage = (event) => {
            const message: TelemetryMessage = JSON.parse(event.data);
            console.log(message);
            updateTelemetry(message);
            console.log(useRovStore.getState());
        };

        ws.onclose = () => {
            console.log("WebSocket connection closed.");
        };

        ws.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        return () => {
            console.log("Closing websocket connection...");
            ws.close();
        };
    }, []);
};
