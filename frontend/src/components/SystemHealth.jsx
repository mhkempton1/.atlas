import React, { useState, useEffect } from 'react';
import { SYSTEM_API } from '../services/api';

const SystemHealth = () => {
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchHealth = async () => {
        try {
            const data = await SYSTEM_API.checkHealth();
            setHealth(data);
        } catch {
            setHealth({ altimeter: "disconnected" });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHealth();
        const interval = setInterval(fetchHealth, 30000); // 30s
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="text-xs text-gray-500">Systems Normal...</div>;

    const isConnected = health?.altimeter === 'connected';

    return (
        <div
            onClick={() => window.open('http://localhost:4204', '_blank')}
            className={`p-2 rounded-md border flex items-center gap-2 cursor-pointer transition-all hover:scale-105 active:scale-95 ${isConnected ? 'bg-green-50/50 border-green-500/30' : 'bg-red-50/50 border-red-500/30'}`}
            title="Click to Port-In to Altimeter"
        >
            <div className={`w-2 h-2 rounded-full animate-pulse ${isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'}`}></div>
            <div className="flex flex-col">
                <span className="text-[10px] font-bold text-text-bright tracking-wider uppercase">Altimeter Context</span>
                <span className="text-[9px] text-text-muted">
                    {isConnected ? 'PORT-IN READY' : 'RE-BOOT REQ'}
                </span>
            </div>
        </div>
    );
};

export default SystemHealth;
