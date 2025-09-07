// For managing the WebSocket connection

import { useEffect } from "react";
import useRovStore from "../store/rovStore";
import type { TelemetryMessage } from "../types";

export const useTelemetry = () => {
    const updateTelemetry = useRovStore((state) => state.updateTelemetry);
    const telemetry = useRovStore((state) => state);

    useEffect(() => {
        console.log("Attempting to connect...");

        const ws = new WebSocket("ws://localhost:8000/ws/telemetry");

        ws.onopen = () => {
            console.log("Websocket connection established");
        };

        ws.onmessage = (event) => {
            const message: TelemetryMessage = JSON.parse(event.data);
            console.log(message);
            updateTelemetry(message);
            console.log(telemetry);
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
