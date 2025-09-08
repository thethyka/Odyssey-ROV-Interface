import { useState } from "react";
import MissionLogModal from "./MissionLogModal";

export default function MissionLogButton() {
    const [open, setOpen] = useState(false);

    return (
        <div className="w-full flex justify-center p-4 mt-auto">
            <button
                onClick={() => setOpen(true)}
                className="px-4 py-2 rounded-lg bg-component border border-border text-text-primary hover:bg-info transition-colors"
            >
                Mission Log
            </button>

            {open && <MissionLogModal onClose={() => setOpen(false)} />}
        </div>
    );
}
