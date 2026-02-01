import React, { useState, useEffect } from 'react';
import { ShieldCheck, Server, Database, Activity, HardDrive, Power, Play, VolumeX, ExternalLink } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';

const SystemHealthView = () => {
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(null);

    const loadHealth = async () => {
        const data = await SYSTEM_API.checkHealth();
        setHealth(data);
        setLoading(false);
    };

    useEffect(() => {
        loadHealth();
        const interval = setInterval(loadHealth, 10000); // 10s refresh
        return () => clearInterval(interval);
    }, []);

    const handleAction = async (action) => {
        setActionLoading(action);
        try {
            await SYSTEM_API.triggerAction(action);
            // Give it 2 seconds then refresh
            setTimeout(loadHealth, 2000);
        } catch (e) {
            alert(`Action failed: ${e.message}`);
        } finally {
            setActionLoading(null);
        }
    };

    if (loading) return <div className="p-10 text-center animate-pulse">Scanning System Vitals...</div>;

    const altOnline = health?.altimeter_core === 'connected';
    const atlasOnline = health?.atlas_backend === 'operational';

    return (
        <div className="p-6 bg-surface-dark rounded-lg border border-border">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                    <Activity className="w-6 h-6 text-primary" />
                    <h2 className="text-xl font-bold text-text-bright">System Health & Command Center</h2>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={() => handleAction('shutdown')}
                        disabled={actionLoading}
                        className="px-3 py-1.5 rounded bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20 text-xs font-bold flex items-center gap-2"
                        title="Kill all project processes"
                    >
                        <Power className="w-3 h-3" /> SHUTDOWN
                    </button>
                    <button
                        onClick={() => handleAction('boot-silent')}
                        disabled={actionLoading}
                        className="px-3 py-1.5 rounded bg-slate-700/50 text-slate-300 border border-slate-600 hover:bg-slate-700 text-xs font-bold flex items-center gap-2"
                        title="Silent start (0 windows)"
                    >
                        <VolumeX className="w-3 h-3" /> SILENT BOOT
                    </button>
                    <button
                        onClick={() => handleAction('boot-all')}
                        disabled={actionLoading}
                        className="px-3 py-1.5 rounded bg-primary/20 text-primary border border-primary/30 hover:bg-primary/30 text-xs font-bold flex items-center gap-2"
                        title="Full start (2 log windows)"
                    >
                        <Play className="w-3 h-3" /> FULL LAUNCH
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <StatusCard
                    icon={Server}
                    label="Atlas Backend"
                    value={atlasOnline ? 'Online' : 'Offline'}
                    status={atlasOnline ? 'success' : 'error'}
                />
                <StatusCard
                    icon={Database}
                    label="Altimeter Core"
                    value={altOnline ? 'Connected' : 'Disconnected'}
                    sub={altOnline ? 'Link Stable' : (health?.details?.altimeter_error || 'Link Severed')}
                    status={altOnline ? 'success' : 'error'}
                />
                <StatusCard
                    icon={ShieldCheck}
                    label="Security"
                    value="Enforced"
                    sub="Strata 5 active"
                    status={'success'}
                />
                <StatusCard
                    icon={ExternalLink}
                    label="Altimeter UI"
                    value="Port-In"
                    onClick={() => window.open('http://127.0.0.1:4204', '_blank')}
                    sub="Open Browser Site"
                    status={'neutral'}
                />
            </div>

            <div className="bg-background-dark p-6 rounded-lg border border-border">
                <h3 className="text-sm font-semibold text-text-muted mb-4 uppercase tracking-wider">Environment Details</h3>
                <div className="space-y-3">
                    <div className="flex justify-between border-b border-border/10 pb-2">
                        <span className="text-text-muted text-xs">Altimeter Endpoint</span>
                        <span className="font-mono text-text-bright text-xs">http://127.0.0.1:4203</span>
                    </div>
                    <div className="flex justify-between border-b border-border/10 pb-2">
                        <span className="text-text-muted text-xs">Atlas Endpoint</span>
                        <span className="font-mono text-text-bright text-xs">http://127.0.0.1:4201</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatusCard = ({ icon, label, value, sub, status, onClick }) => {
    const Icon = icon;
    const colors = {
        success: 'text-green-400 bg-green-400/10 border-green-400/20',
        warning: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
        error: 'text-red-400 bg-red-400/10 border-red-400/20',
        neutral: 'text-blue-400 bg-blue-400/10 border-blue-400/20 hover:bg-blue-400/20 cursor-pointer'
    };

    const colorClass = colors[status] || colors.neutral;

    return (
        <div
            onClick={onClick}
            className={`p-4 rounded-lg border ${colorClass} flex flex-col items-center justify-center text-center transition-all`}
        >
            <Icon className="w-8 h-8 mb-2 opacity-80" />
            <div className="text-xs uppercase tracking-wider opacity-70 mb-1">{label}</div>
            <div className="text-lg font-bold">{value}</div>
            {sub && <div className="text-[10px] mt-1 opacity-60 font-mono">{sub}</div>}
        </div>
    );
};

export default SystemHealthView;
