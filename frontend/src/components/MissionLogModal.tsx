import { useEffect, useState } from "react";

interface LogEntry {
    timestamp: string;
    level: "INFO" | "WARNING" | "CRITICAL" | "OPERATOR";
    message: string;
}

export default function MissionLogModal({ onClose }: { onClose: () => void }) {
    const [entries, setEntries] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchLogs() {
            try {
                // 🔒 Hardcoded endpoint
                const res = await fetch("http://localhost:8000/mission-log");
                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                const data = await res.json();
                setEntries(data || []);
            } catch (err) {
                console.error("Failed to fetch mission log", err);
            } finally {
                setLoading(false);
            }
        }

        fetchLogs();
    }, []);

    const levelColorMap: { [key: string]: string } = {
        INFO: "text-info",
        WARNING: "text-warning",
        CRITICAL: "text-critical",
        OPERATOR: "text-text-secondary",
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="w-[600px] max-h-[80vh] bg-surface rounded-lg border border-border p-6 flex flex-col">
                {/* Header */}
                <div className="flex justify-between items-center mb-4">
                    <h2 className="font-sans font-semibold text-lg text-text-primary">
                        Mission Log
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-text-secondary hover:text-text-primary"
                    >
                        ✕
                    </button>
                </div>

                {/* Content */}
                {loading ? (
                    <p className="text-text-secondary">Loading...</p>
                ) : entries.length === 0 ? (
                    <p className="text-text-secondary">
                        No log entries available.
                    </p>
                ) : (
                    <div className="overflow-y-auto flex-1 space-y-2 pr-2">
                        {entries.map((entry, idx) => (
                            <div
                                key={idx}
                                className={`font-mono text-sm border-b border-border pb-1 ${
                                    levelColorMap[entry.level]
                                }`}
                            >
                                <span className="text-text-secondary mr-2">
                                    [{entry.timestamp}]
                                </span>
                                <span className="uppercase mr-2">
                                    {entry.level}
                                </span>
                                {entry.message}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
