import React, { useState, useEffect } from 'react';
import { Server, Activity, Calendar, Database, AlertTriangle, CheckCircle, Copy, Clock, Zap, ChevronDown, ChevronUp, Shield, Wifi } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';
import { Spinner } from '../shared/UIComponents';

const getHealthColor = (percentage) => {
    const yellow = { r: 252, g: 211, b: 77 };
    const green = { r: 16, g: 185, b: 129 };
    const r = Math.round(yellow.r + (green.r - yellow.r) * (percentage / 100));
    const g = Math.round(yellow.g + (green.g - yellow.g) * (percentage / 100));
    const b = Math.round(yellow.b + (green.b - yellow.b) * (percentage / 100));
    return `rgb(C:\Users\mhkem\.atlas\frontend{r}, C:\Users\mhkem\.atlas\frontend{g}, C:\Users\mhkem\.atlas\frontend{b})`;
};

const SystemStatusView = ({ onNavigate }) => {
    const [healthData, setHealthData] = useState(null);
    const [activityLogs, setActivityLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [copiedCommand, setCopiedCommand] = useState(null);
    const [expandedSections, setExpandedSections] = useState({ remediation: true, nodes: true, logs: true, internal: true });

    useEffect(() => {
        loadSystemData();
        const interval = setInterval(loadSystemData, 30000);
        return () => clearInterval(interval);
    }, []);

    const loadSystemData = async () => {
        try {
            const health = await SYSTEM_API.checkHealth();
            setHealthData(health);
            setActivityLogs([]);
        } catch (error) {
            console.error('Failed to load system data:', error);
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = (text, id) => {
        navigator.clipboard.writeText(text);
        setCopiedCommand(id);
        setTimeout(() => setCopiedCommand(null), 2000);
    };

    const toggleSection = (section) => {
        setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

    const getIconComponent = (iconName) => {
        const icons = { server: Server, activity: Activity, calendar: Calendar, database: Database };
        return icons[iconName] || Server;
    };

    if (loading) return <Spinner label='Loading System Status...' />;
    if (!healthData) return <div className='p-8 text-white/60'>Failed to load system data</div>;

    const degradedSystems = healthData.subsystems?.filter(s => !s.healthy) || [];
    const healthPercentage = healthData.health_percentage || 0;
    const healthColor = getHealthColor(healthPercentage);

    return (
        <div className='min-h-screen flex flex-col animate-slide-in bg-transparent'>
            <div className='px-8 py-6 border-b border-white/10 bg-white/[0.02]'>
                <div className='flex justify-between items-center'>
                    <div>
                        <h1 className='text-4xl font-mono font-medium tracking-[0.2em] text-white uppercase'>System Status</h1>
                        <p className='text-sm text-white/40 font-mono mt-2'>Real-time diagnostics and monitoring</p>
                    </div>
                    <div className='flex items-center gap-6'>
                        <div className='text-right'>
                            <p className='text-xs text-white/40 font-mono uppercase'>Overall Health</p>
                            <p className='text-5xl font-mono font-bold' style={{ color: healthColor }}>{healthPercentage}%</p>
                        </div>
                        <div className='w-20 h-20 rounded-2xl border-4 flex items-center justify-center' style={{ borderColor: healthColor, backgroundColor: `C:\Users\mhkem\.atlas\frontend{healthColor}20` }}>
                            <Activity className='w-10 h-10' style={{ color: healthColor }} />
                        </div>
                    </div>
                </div>
            </div>
            <div className='flex-1 px-8 py-6 space-y-6 overflow-y-auto custom-scrollbar'>
                {degradedSystems.length > 0 && (
                    <div className='bg-amber-500/10 border border-amber-500/30 rounded-2xl overflow-hidden'>
                        <div className='p-6 cursor-pointer hover:bg-amber-500/5 transition-colors flex justify-between items-center' onClick={() => toggleSection('remediation')}>
                            <div className='flex items-center gap-4'>
                                <AlertTriangle className='w-6 h-6 text-amber-400' />
                                <div>
                                    <h2 className='text-xl font-mono font-medium text-amber-400'>REMEDIATION REQUIRED</h2>
                                    <p className='text-sm text-white/60 mt-1'>{degradedSystems.length} subsystem{degradedSystems.length > 1 ? 's' : ''} degraded</p>
                                </div>
                            </div>
                            {expandedSections.remediation ? <ChevronUp className='w-5 h-5 text-white/40' /> : <ChevronDown className='w-5 h-5 text-white/40' />}
                        </div>
                        {expandedSections.remediation && (
                            <div className='p-6 pt-0 space-y-4'>
                                {degradedSystems.map((system, idx) => (
                                    system.remediation && (
                                        <div key={idx} className='p-5 bg-black/40 rounded-xl border border-white/5'>
                                            <h4 className='text-lg font-medium text-white mb-3'>{system.name}: {system.remediation.title}</h4>
                                            <ol className='space-y-2 mb-4'>
                                                {system.remediation.steps.map((step, stepIdx) => (
                                                    <li key={stepIdx} className='text-sm text-white/70 font-mono flex items-start gap-3'>
                                                        <span className='text-cyan-400 font-bold'>{stepIdx + 1}.</span>
                                                        <span>{step}</span>
                                                    </li>
                                                ))}
                                            </ol>
                                            {system.remediation.command && (
                                                <div className='flex items-center gap-3'>
                                                    <code className='flex-1 px-4 py-3 bg-black/60 border border-white/10 rounded-lg text-sm text-cyan-400 font-mono'>{system.remediation.command}</code>
                                                    <button onClick={() => copyToClipboard(system.remediation.command, `cmd-C:\Users\mhkem\.atlas\frontend{idx}`)} className='px-4 py-3 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white transition-colors flex items-center gap-2'>
                                                        <Copy className='w-4 h-4' />
                                                        {copiedCommand === `cmd-C:\Users\mhkem\.atlas\frontend{idx}` ? 'Copied!' : 'Copy'}
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    )
                                ))}
                            </div>
                        )}
                    </div>
                )}
                <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
                    <div className='bg-white/5 border border-white/10 rounded-2xl p-6'>
                        <div className='flex items-center gap-4 mb-6'>
                            <Clock className='w-6 h-6 text-cyan-400' />
                            <h3 className='text-xl font-mono font-medium text-white uppercase'>System Uptime</h3>
                        </div>
                        <div className='grid grid-cols-2 gap-6'>
                            <div>
                                <p className='text-xs text-white/40 font-mono uppercase mb-2'>Current Uptime</p>
                                <p className='text-3xl font-mono font-bold text-cyan-400'>{healthData.uptime_formatted || '0h 0m'}</p>
                            </div>
                            <div>
                                <p className='text-xs text-white/40 font-mono uppercase mb-2'>Last Restart</p>
                                <p className='text-sm font-mono text-white/80'>{healthData.server_start ? new Date(healthData.server_start).toLocaleString() : 'Unknown'}</p>
                            </div>
                        </div>
                    </div>
                    <div className='bg-white/5 border border-white/10 rounded-2xl p-6'>
                        <div className='flex items-center gap-4 mb-6'>
                            <Zap className='w-6 h-6 text-cyan-400' />
                            <h3 className='text-xl font-mono font-medium text-white uppercase'>Subsystems ({healthData.subsystems?.length || 0})</h3>
                        </div>
                        <div className='space-y-3'>
                            {healthData.subsystems?.map((system, idx) => {
                                const IconComponent = getIconComponent(system.icon);
                                return (
                                    <div key={idx} className='flex items-center justify-between p-3 bg-white/[0.03] rounded-xl border border-white/5'>
                                        <div className='flex items-center gap-3'>
                                            <IconComponent className={`w-5 h-5 C:\Users\mhkem\.atlas\frontend{system.healthy ? 'text-cyan-400' : 'text-amber-400'}`} />
                                            <span className='text-white/80'>{system.name}</span>
                                        </div>
                                        <div className='flex items-center gap-2'>
                                            {system.healthy ? <CheckCircle className='w-5 h-5 text-cyan-400' /> : <AlertTriangle className='w-5 h-5 text-amber-400' />}
                                            <span className={`text-xs font-mono uppercase C:\Users\mhkem\.atlas\frontend{system.healthy ? 'text-cyan-400' : 'text-amber-400'}`}>{system.status}</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Node Diagnostics */}
                <div className='bg-white/5 border border-white/10 rounded-2xl overflow-hidden'>
                    <div className='p-6 cursor-pointer hover:bg-white/[0.03] transition-colors flex justify-between items-center' onClick={() => toggleSection('nodes')}>
                        <div className='flex items-center gap-4'>
                            <Server className='w-6 h-6 text-cyan-400' />
                            <h3 className='text-xl font-mono font-medium text-white uppercase'>Node Diagnostics</h3>
                        </div>
                        {expandedSections.nodes ? <ChevronUp className='w-5 h-5 text-white/40' /> : <ChevronDown className='w-5 h-5 text-white/40' />}
                    </div>
                    {expandedSections.nodes && (
                        <div className='p-6 pt-0 grid grid-cols-1 md:grid-cols-2 gap-4'>
                            {[
                                { name: 'Atlas Primary Server', status: 'ACTIVE', load: '12%', healthy: true },
                                { name: 'Altimeter Data Node', status: 'SYNCED', load: '04%', healthy: true },
                                { name: 'Matrix Logic Core', status: 'ONLINE', load: '42%', healthy: true },
                                { name: 'Encryption Bridge', status: 'ACTIVE', load: '01%', healthy: true }
                            ].map((node, idx) => (
                                <div key={idx} className='p-4 bg-white/[0.03] rounded-xl border border-white/5 hover:bg-white/10 transition-all'>
                                    <div className='flex justify-between items-center'>
                                        <div className='flex items-center gap-3'>
                                            <Server className='w-5 h-5 text-white/40' />
                                            <p className='text-sm text-white/80 font-medium'>{node.name}</p>
                                        </div>
                                        <div className='text-right'>
                                            <p className='text-xs font-mono font-bold text-cyan-400'>{node.status}</p>
                                            <p className='text-[10px] text-white/30 font-mono'>{node.load} UTIL</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Internal Diagnostics */}
                <div className='bg-white/5 border border-white/10 rounded-2xl overflow-hidden'>
                    <div className='p-6 cursor-pointer hover:bg-white/[0.03] transition-colors flex justify-between items-center' onClick={() => toggleSection('internal')}>
                        <div className='flex items-center gap-4'>
                            <Shield className='w-6 h-6 text-cyan-400' />
                            <h3 className='text-xl font-mono font-medium text-white uppercase'>Internal Diagnostics</h3>
                        </div>
                        {expandedSections.internal ? <ChevronUp className='w-5 h-5 text-white/40' /> : <ChevronDown className='w-5 h-5 text-white/40' />}
                    </div>
                    {expandedSections.internal && (
                        <div className='p-6 pt-0 grid grid-cols-2 md:grid-cols-4 gap-4'>
                            <div className='p-4 bg-white/[0.03] rounded-xl border border-white/5'>
                                <p className='text-xs text-white/40 font-mono uppercase mb-2'>Secure Link</p>
                                <p className='text-lg font-mono font-bold text-cyan-400'>ESTABLISHED</p>
                            </div>
                            <div className='p-4 bg-white/[0.03] rounded-xl border border-white/5'>
                                <p className='text-xs text-white/40 font-mono uppercase mb-2'>Data Stream</p>
                                <p className='text-lg font-mono font-bold text-cyan-400'>4.2 GB/S</p>
                            </div>
                            <div className='p-4 bg-white/[0.03] rounded-xl border border-white/5'>
                                <p className='text-xs text-white/40 font-mono uppercase mb-2'>Signal Ping</p>
                                <p className='text-lg font-mono font-bold text-cyan-400'>12 MS</p>
                            </div>
                            <div className='p-4 bg-white/[0.03] rounded-xl border border-white/5'>
                                <p className='text-xs text-white/40 font-mono uppercase mb-2'>Encryption</p>
                                <p className='text-lg font-mono font-bold text-cyan-400'>ENHANCED</p>
                            </div>
                        </div>
                    )}
                    {expandedSections.internal && (
                        <div className='px-6 pb-6'>
                            <div className='p-4 bg-black/40 rounded-xl border border-cyan-500/20 flex items-center justify-center'>
                                <Wifi className='w-4 h-4 text-cyan-400 mr-2' />
                                <p className='text-sm font-mono text-cyan-400'>Atlas Protocol V5.2</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SystemStatusView;
