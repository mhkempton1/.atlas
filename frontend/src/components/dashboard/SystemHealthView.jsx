import React, { useState, useEffect } from 'react';
import { ShieldCheck, Server, Database, Activity, HardDrive, Power, Play, VolumeX, ExternalLink, Mail } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';

import usePersistentState from '../../hooks/usePersistentState';

const SystemHealthView = () => {
    const [actionLoading, setActionLoading] = useState(null);

    // Persistent State Hooks
    const [health, isHealthLoading] = usePersistentState('system_health_core', () => SYSTEM_API.checkHealth().catch(() => ({ status: 'offline' })), { status: 'offline' });
    const [logs, isLogsLoading] = usePersistentState('system_logs_stream', () => SYSTEM_API.getSystemLogs().catch(() => []), []);
    const [emailStats, isStatsLoading] = usePersistentState('system_email_stats', () => SYSTEM_API.getEmailStats().catch(() => ({ total_emails: 0, unread_emails: 0 })), { total_emails: 0, unread_emails: 0 });

    const loadHealth = async () => {
        // usePersistentState handles refresh through its internal mechanisms,
        // but we can trigger a manual refresh if needed or rely on its polling.
        // For SystemHealthView, we'll keep it simple and let the hook handle it.
    };

    useEffect(() => {
        // Polling is handled by usePersistentState if it's configured for it, 
        // or we can add a simple refresh trigger here if preferred.
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

    if (isHealthLoading && !health.subsystems) return <div className="p-10 text-center animate-pulse font-mono text-cyan-400">ACCESSING_LOGIC_CORE...</div>;

    const altOnline = health?.altimeter_core === 'connected' || health.subsystems?.some(s => s.name === "Altimeter Core" && s.healthy);
    const atlasOnline = health?.atlas_backend === 'operational' || health.subsystems?.some(s => s.name === "Atlas Backend" && s.healthy);

    return (
        <div className="p-8 bg-transparent min-h-screen flex flex-col space-y-8">
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

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
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
                    icon={Mail}
                    label="Communications"
                    value={emailStats?.total_emails?.toLocaleString() || '0'}
                    sub={`${emailStats?.unread_emails || 0} Packets Pending`}
                    status={'neutral'}
                />
                <StatusCard
                    icon={ShieldCheck}
                    label="Strata Security"
                    value="Enforced"
                    sub="Strata 5 active"
                    status={'success'}
                />
                <StatusCard
                    icon={ExternalLink}
                    label="Integrations"
                    value="Altimeter UI"
                    onClick={() => window.open('http://127.0.0.1:4204', '_blank')}
                    sub="Legacy Dashboard"
                    status={'neutral'}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Environment Details */}
                <div className="bg-white/[0.02] p-8 rounded-3xl border border-white/10 backdrop-blur-xl h-full">
                    <h3 className="text-xs font-mono font-bold text-white/30 mb-6 uppercase tracking-[0.3em]">Environment Signals</h3>
                    <div className="space-y-4">
                        <div className="flex justify-between border-b border-white/5 pb-3">
                            <span className="text-white/40 text-xs font-mono uppercase">Altimeter Endpoint</span>
                            <span className="font-mono text-cyan-400 text-xs tracking-wider">http://...:4203</span>
                        </div>
                        <div className="flex justify-between border-b border-white/5 pb-3">
                            <span className="text-white/40 text-xs font-mono uppercase">Atlas Endpoint</span>
                            <span className="font-mono text-cyan-400 text-xs tracking-wider">http://...:4201</span>
                        </div>
                        <div className="flex justify-between border-b border-white/5 pb-3">
                            <span className="text-white/40 text-xs font-mono uppercase">System Uptime</span>
                            <span className="font-mono text-white/70 text-xs tracking-wider">{health.uptime_formatted || '0h 0m'}</span>
                        </div>
                    </div>
                </div>

                {/* System Activity Logs */}
                <div className="lg:col-span-2 bg-white/[0.02] border border-white/10 rounded-3xl p-8 flex flex-col backdrop-blur-3xl h-[400px]">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xs font-mono font-bold text-white/30 uppercase tracking-[0.3em]">Temporal Log Stream</h3>
                        <div className="flex gap-2">
                            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                            <span className="text-[10px] font-mono text-cyan-400/60 uppercase">Live Feed</span>
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2 pr-4">
                        {logs && logs.length > 0 ? logs.map((log, i) => (
                            <div key={log.id || i} className="flex gap-4 items-start p-3 bg-white/[0.01] border border-white/5 rounded-xl hover:bg-white/5 transition-colors group">
                                <span className="font-mono text-[10px] text-white/20 whitespace-nowrap mt-0.5">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded ${log.type === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-cyan-500/10 text-cyan-400'}`}>
                                            {log.type}
                                        </span>
                                        <span className="text-xs font-medium text-white/80">{log.action}</span>
                                    </div>
                                    <p className="text-[11px] text-white/40 font-mono italic">{log.target} :: {log.details || 'No additional telemetry'}</p>
                                </div>
                            </div>
                        )) : (
                            <div className="h-full flex items-center justify-center text-white/20 font-mono italic text-sm">
                                NO_ACTIVITY_DETECTED_IN_SECTOR
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatusCard = ({ icon, label, value, sub, status, onClick }) => {
    const Icon = icon;
    const colors = {
        success: 'text-cyan-400 bg-cyan-400/5 border-cyan-400/20 shadow-[0_0_15px_rgba(34,211,238,0.05)]',
        warning: 'text-amber-400 bg-amber-400/5 border-amber-400/20 shadow-[0_0_15px_rgba(251,191,36,0.05)]',
        error: 'text-red-400 bg-red-400/5 border-red-400/20 shadow-[0_0_15px_rgba(248,113,113,0.05)]',
        neutral: 'text-white/70 bg-white/[0.01] border-white/10 hover:bg-white/[0.04] cursor-pointer'
    };

    const colorClass = colors[status] || colors.neutral;

    return (
        <div
            onClick={onClick}
            className={`p-6 rounded-2xl border ${colorClass} flex flex-col items-center justify-center text-center transition-all backdrop-blur-xl group hover:scale-[1.02]`}
        >
            <div className={`p-3 rounded-xl bg-white/5 mb-4 group-hover:scale-110 transition-transform`}>
                <Icon className="w-6 h-6" />
            </div>
            <div className="text-[10px] uppercase font-mono tracking-[0.2em] opacity-40 mb-2">{label}</div>
            <div className="text-2xl font-mono font-medium tracking-tight whitespace-nowrap">{value}</div>
            {sub && <div className="text-[9px] mt-3 opacity-30 font-mono uppercase tracking-widest truncate w-full">{sub}</div>}
        </div>
    );
};

export default SystemHealthView;
