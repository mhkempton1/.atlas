import React, { useState, useEffect } from 'react';
import {
    Mail, FileText, Settings, Clock, Activity, LayoutDashboard,
    Server, ListTodo, Calendar, Zap, AlertTriangle, CheckCircle,
    BookOpen, Sun, Cloud, CloudRain, Wind, ChevronDown, ChevronUp,
    MessageSquare, Send, X, ExternalLink, ArrowDown, History as HistoryIcon,
    CheckSquare, Menu, Shield
} from 'lucide-react';
import { SYSTEM_API } from '../../services/api';
import { Spinner } from '../shared/UIComponents';
import { useToast } from '../../hooks/useToast';
import { motion as _motion, AnimatePresence } from 'framer-motion';
import MissionIntelWidget from './MissionIntelWidget';
import MissionBriefing from './MissionBriefing';
import usePersistentState from '../../hooks/usePersistentState';

const TelemetryBar = React.memo(({ healthDetails, weather, coordinates }) => {
    const lat = coordinates?.lat ?? 37.04;
    const lon = coordinates?.lon ?? -93.29;

    // Calculate actual health percentage from subsystems
    const calculateHealthPercentage = () => {
        if (!healthDetails) return 0;
        // If we have a direct percentage, use it (from backend)
        if (healthDetails.health_percentage) return healthDetails.health_percentage;

        const subsystems = [
            healthDetails.atlas_backend,
            healthDetails.altimeter_core,
            healthDetails.scheduler,
            healthDetails.database
        ];

        const healthyCount = subsystems.filter(s =>
            s === 'operational' || s === 'connected' || s === 'healthy'
        ).length;

        return Math.round((healthyCount / subsystems.length) * 100);
    };

    const healthPercentage = calculateHealthPercentage();
    const isHealthy = healthDetails?.status === 'online' || healthPercentage >= 90;

    return (
        <div className="w-full flex items-center justify-end px-8 py-2 border-b border-white/5 bg-white/[0.01] backdrop-blur-md text-[10px] font-mono tracking-[0.25em] text-white/40 mb-1">
            <div className="flex items-center gap-16">
                <div className="flex items-center gap-2">
                    <span className="opacity-40 uppercase">Local Temporal Sync ::</span>
                    <span className="text-white/60">{weather?.updated_at || '--:--:--'}</span>
                </div>
                <div className="flex items-center gap-2 ml-4">
                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-500/50 animate-ping" />
                    <span className="text-cyan-500/60 uppercase">Live Feed</span>
                </div>
            </div>
        </div>
    );
}); // End TelemetryBar


const StatCard = React.memo(({ label, value, sub, icon, onClick, trend, color = "text-white" }) => {
    const Icon = icon;
    const isCyan = color.includes('cyan') || color.includes('emerald') || color.includes('blue');
    const isAmber = color.includes('amber') || color.includes('yellow');
    const borderClass = isCyan ? 'border-cyan-500/20' : isAmber ? 'border-amber-500/20' : 'border-white/10';

    return (
        <button
            onClick={onClick}
            className={`relative p-8 cursor-pointer hover:bg-white/5 transition-all group border-l-2 ${borderClass} bg-white/[0.01] backdrop-blur-xl text-left flex flex-col w-full`}
        >
            <div className="flex justify-between items-start mb-4 w-full">
                <div className={`p-3 rounded-xl bg-white/[0.05] border border-white/10 group-hover:border-primary/50 transition-colors ${color}`}>
                    <Icon className="w-8 h-8" />
                </div>
                {trend && (
                    <span className={`text-[12px] font-mono px-3 py-1 uppercase tracking-tighter ${trend === 'up' ? 'text-cyan-400' : 'text-amber-400'}`}>
                        {trend === 'up' ? '>> OPTIMAL' : '>> ALERT'}
                    </span>
                )}
            </div>
            <div className="mt-4">
                <h3 className="text-4xl font-mono font-medium text-white mb-3 tracking-tight">{value}</h3>
                <p className="text-[12px] text-white/50 uppercase tracking-[0.3em] font-medium">{label}</p>
                {sub && <p className="text-[11px] text-white/30 mt-4 font-mono italic truncate w-full">NODE_STREAM :: {sub}</p>}
            </div>
            <div className="absolute right-0 top-[15%] bottom-[15%] w-[1px] bg-white/5 hidden lg:block" />
        </button>
    );
});

// Memoized Weather Component
const WeatherForecast = React.memo(({ forecast, loading, onRetry, error }) => {
    if (loading) {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 opacity-50">
                {[...Array(7)].map((_, i) => (
                    <div key={i} className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center animate-pulse">
                        <div className="h-3 w-12 bg-white/10 rounded mx-auto mb-3" />
                        <div className="h-8 w-8 bg-white/10 rounded-full mx-auto mb-3" />
                        <div className="h-6 w-16 bg-white/10 rounded mx-auto" />
                    </div>
                ))}
            </div>
        );
    }

    if (!forecast || forecast.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-8 gap-4 w-full">
                <div className={`font-mono italic text-center ${error ? 'text-red-400 font-bold' : 'text-white/30'}`}>
                    {error ? `CONNECTION FAILURE :: ${error}` : 'Awaiting environmental telemetry uplink...'}
                </div>
                {onRetry && (
                    <button
                        onClick={(e) => { e.stopPropagation(); onRetry(); }}
                        className={`px-6 py-2 border rounded-lg text-xs font-mono uppercase tracking-widest transition-all flex items-center gap-2 ${error ? 'bg-red-500/10 border-red-500/30 text-red-400 hover:bg-red-500/20' : 'bg-cyan-500/10 hover:bg-cyan-500/20 border-cyan-500/30 text-cyan-400'}`}
                    >
                        <Activity className="w-4 h-4" /> {error ? 'RETRY CONNECTION' : 'Initialize Uplink'}
                    </button>
                )}
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            {forecast.map((day, i) => (
                <div key={i} className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center hover:bg-white/[0.05] transition-colors group">
                    <p className="text-[11px] uppercase font-bold text-white/30 mb-3 group-hover:text-cyan-400 transition-colors">{day.display_date}</p>
                    <div className="flex justify-center mb-3 h-10 items-center">
                        {(day.condition.includes('Sunny') || day.condition.includes('Clear')) && <Sun className="w-8 h-8 text-yellow-500/80 animate-pulse" />}
                        {(day.condition.includes('Cloudy') || day.condition.includes('Fog')) && <Cloud className="w-8 h-8 text-white/40" />}
                        {(day.condition.includes('Rain') || day.condition.includes('Storm') || day.condition.includes('Shower')) && <CloudRain className="w-8 h-8 text-cyan-400/60" />}
                        {(!day.condition.includes('Sunny') && !day.condition.includes('Clear') && !day.condition.includes('Cloudy') && !day.condition.includes('Fog') && !day.condition.includes('Rain') && !day.condition.includes('Storm') && !day.condition.includes('Shower')) && <Activity className="w-6 h-6 text-white/20" />}
                    </div>
                    <div className="text-xl font-mono font-medium text-white mb-1">{day.high}°</div>
                    <div className="text-[10px] text-white/30 font-mono">{day.low}°</div>
                    <div className="mt-3 pt-3 border-t border-white/5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <p className="text-[9px] text-cyan-400/60 uppercase font-mono">{day.condition}</p>
                    </div>
                </div>
            ))}
        </div>
    );
});

// Unified Task/Calendar Item
const MissionItem = ({ item, onNavigate }) => {
    const isTask = item.type === 'task';
    const isAltimeter = item.type === 'altimeter';

    return (
        <button
            onClick={() => onNavigate(isTask ? 'tasks' : isAltimeter ? 'projects' : 'calendar_google')}
            className={`p-6 bg-white/[0.02] border border-white/10 rounded-2xl hover:bg-white/[0.05] hover:border-cyan-500/30 transition-all cursor-pointer group flex flex-col w-full text-left ${!isTask ? 'border-l-4 border-l-cyan-500/40' : ''}`}
        >
            <div className="flex justify-between items-start mb-5 w-full">
                <div className={`p-3 rounded-lg ${isTask ? 'bg-amber-500/10 text-amber-500' : isAltimeter ? 'bg-cyan-500/10 text-cyan-400' : 'bg-purple-500/10 text-purple-400'}`}>
                    {isTask ? <CheckSquare className="w-5 h-5" /> : isAltimeter ? <Shield className="w-5 h-5" /> : <Clock className="w-5 h-5" />}
                </div>
                <span className={`text-[10px] font-mono px-2.5 py-1 rounded border ${isTask ? (item.deviation > 0 ? 'border-amber-500/40 text-amber-500' : 'border-cyan-500/20 text-cyan-500') : (isAltimeter ? 'border-cyan-500/20 text-cyan-500' : 'border-purple-500/20 text-purple-500')}`}>
                    {isTask ? (item.deviation > 0 ? `SLIPPAGE :: +${item.deviation}D` : 'STATUS :: OPTIMAL') : isAltimeter ? 'MILESTONE' : 'TEMPORAL_EVENT'}
                </span>
            </div>
            <h4 className="text-xl font-medium text-white mb-3 group-hover:text-cyan-400 transition-colors leading-tight">{item.name}</h4>
            <div className="flex justify-between items-center mt-6 pt-4 border-t border-white/5 opacity-50 w-full">
                <p className="text-[10px] font-mono uppercase">{isTask ? `Sector :: ${item.project_id || 'Core'}` : isAltimeter ? 'Altimeter Sync' : `Start :: ${item.current_start}`}</p>
                <p className="text-[10px] font-mono">{isTask ? (item.original_due_date || item.current_start) : 'Calendar Sync'}</p>
            </div>
        </button>
    );
};

const ChatBot = React.memo(({ onNavigate }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([{ role: 'bot', text: 'Ethereal Console Intelligence active. Direct linking to Sector Protocols established.' }]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSend = async () => {
        if (!input.trim()) return;
        const userMsg = input;
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setInput('');
        setLoading(true);
        try {
            const res = await SYSTEM_API.sendMessage(userMsg);
            const botMsg = { role: 'bot', text: res.reply, links: res.links };
            if (res.ui_action) {
                botMsg.ui_component = res.ui_action.component;
            }
            setMessages(prev => [...prev, botMsg]);
        } catch {
            setMessages(prev => [...prev, { role: 'bot', text: "Signal latency exceeded. Connection dropped." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed bottom-8 right-8 z-[100]">
            <AnimatePresence>
                {isOpen && (
                    <_motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 30 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 30 }}
                        className="bg-black/40 backdrop-blur-3xl border border-white/10 w-96 h-[550px] rounded-3xl shadow-[0_0_50px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden mb-6"
                    >
                        <div className="p-6 flex justify-between items-center border-b border-white/10 bg-white/5">
                            <div className="flex items-center gap-3">
                                <Zap className="w-6 h-6 text-cyan-400" />
                                <span className="font-bold text-white tracking-[0.3em] text-sm uppercase">Atlas::Core</span>
                            </div>
                            <button onClick={() => setIsOpen(false)}><X className="w-6 h-6 text-white/40 hover:text-white" /></button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                            {messages.map((m, i) => (
                                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-[85%] p-4 rounded-2xl text-sm ${m.role === 'user' ? 'bg-cyan-600 text-white' : 'bg-white/5 text-gray-300'}`}>
                                        <div dangerouslySetInnerHTML={{ __html: m.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                                    </div>
                                </div>
                            ))}
                            {loading && <div className="text-[10px] text-cyan-400/50 animate-pulse font-mono font-bold tracking-widest">AWAITING_RESPONSE...</div>}
                        </div>
                        <div className="p-6 bg-black/40 border-t border-white/5">
                            <div className="flex gap-3">
                                <input
                                    className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition-all font-mono"
                                    placeholder="Execute query..."
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                />
                                <button onClick={handleSend} className="p-3 bg-cyan-600 rounded-xl text-white hover:bg-cyan-500 transition-colors"><Send className="w-5 h-5" /></button>
                            </div>
                        </div>
                    </_motion.div>
                )}
            </AnimatePresence>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-16 h-16 bg-white/[0.03] backdrop-blur-xl rounded-full shadow-2xl flex items-center justify-center hover:bg-white/10 transition-all hover:scale-105 active:scale-95 border border-white/10"
            >
                {isOpen ? <X className="w-7 h-7 text-white" /> : <MessageSquare className="w-7 h-7 text-white" />}
            </button>
        </div>
    );
});


const Dashboard = ({ onNavigate, globalHealth }) => {
    const { toastElement } = useToast();

    // Persistent State Hooks (Stale-While-Revalidate)
    const [stats, isStatsLoading] = usePersistentState('atlas_stats', () => SYSTEM_API.getDashboardStats().catch(() => ({})), {});
    const [healthDetails, isHealthLoading] = usePersistentState('atlas_health', () => SYSTEM_API.checkHealth().catch(() => ({ status: 'offline' })), { status: 'offline' });
    const [schedule, isScheduleLoading] = usePersistentState('atlas_schedule', () => SYSTEM_API.getUnifiedSchedule().catch(() => []), []);
    const [weather, isWeatherLoading] = usePersistentState('atlas_weather', () => SYSTEM_API.getWeather(37.04, -93.29).catch(() => ({ forecast: [] })), { forecast: [] });

    // UI State
    const [isNodesOpen, setIsNodesOpen] = useState(false);
    const [isMissionFlowOpen, setIsMissionFlowOpen] = useState(true);
    const [isIntelligenceOpen, setIsIntelligenceOpen] = useState(true);
    const [coordinates, setCoordinates] = useState({ lat: 37.04, lon: -93.29 }); // Default Nixa, MO
    const [activeBriefing, setActiveBriefing] = useState(null);

    // Initial Geolocation (Side Effect)
    useEffect(() => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((pos) => {
                const newLat = pos.coords.latitude;
                const newLon = pos.coords.longitude;
                setCoordinates({ lat: newLat, lon: newLon });
            }, (err) => {

            }, { timeout: 3000 });
        }
    }, []);

    // Initial Loading State (Only if no cache exists and we are actually loading)
    const isInitialLoad = isStatsLoading && !stats.inbox_total && schedule.length === 0;

    if (isInitialLoad && isStatsLoading) {
        return <Spinner label="Waking up Ethereal Systems..." />;
    }

    return (
        <div className="min-h-screen flex flex-col animate-slide-in relative overflow-hidden bg-transparent">
            <TelemetryBar healthDetails={healthDetails || globalHealth} weather={weather} coordinates={coordinates} />

            <div className="flex-1 px-8 py-4 flex flex-col space-y-6">
                {/* Header Strip */}
                <div className="flex justify-between items-center border-b border-white/5 pb-4">
                    <div>
                        <h1 className="text-3xl font-mono font-medium tracking-[0.2em] text-white">Assistant Console</h1>
                        <p className="text-[11px] font-mono text-white/30 tracking-[0.4em] uppercase mt-2">Unified Control :: Sector Unified Command</p>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="text-right">
                            <p className="text-[10px] font-mono text-cyan-400/60 uppercase">System Uptime</p>
                            <p className="text-lg font-mono text-white/80">99.98%</p>
                        </div>
                        <div className="flex items-center gap-4">
                            <button className="p-3 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition-all">
                                <Settings className="w-6 h-6 text-white/40" />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Primary Health Hub - Slimmed Scale */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-1 border border-white/10 bg-white/5 rounded-3xl overflow-hidden shadow-2xl">
                    <div
                        className="lg:col-span-12 p-6 space-glow-bg flex flex-col md:flex-row justify-between items-center group cursor-pointer border-b border-white/10"
                        onClick={() => onNavigate('history')}
                    >
                        <div className="flex flex-col gap-2">
                            <div className="flex items-baseline gap-4">
                                <h2 className="text-7xl font-mono font-medium text-white text-high-contrast leading-none">{healthDetails?.status === 'online' ? '100%' : (healthDetails?.health_percentage ? `${healthDetails.health_percentage}%` : '85%')}</h2>
                                <div className="space-y-0.5">
                                    <p className="text-xl text-white/50 font-mono tracking-[0.2em] uppercase">Viability</p>
                                    <p className="text-[10px] text-white/30 font-mono italic text-opacity-20 uppercase tracking-tighter">:: LINK_ESTABLISHED :: NO_DEVIATION_DETECTED</p>
                                </div>
                            </div>
                        </div>
                        <div className="flex flex-col items-end gap-2 text-right">
                            <div className={`p-4 rounded-2xl ${healthDetails?.status === 'online' ? 'bg-cyan-500/10' : 'bg-amber-500/10'} border border-white/10 backdrop-blur-2xl`}>
                                <Activity className={`w-12 h-12 ${healthDetails?.status === 'online' ? 'text-cyan-400 animate-pulse' : 'text-amber-400'}`} />
                            </div>
                            <p className="text-[10px] text-white/40 font-mono tracking-widest uppercase group-hover:text-cyan-400 transition-colors">
                                STATUS :: {healthDetails?.status === 'online' ? 'LINK_SYNCHRONIZED' : 'DEGRADED'}
                            </p>
                        </div>
                    </div>

                    {/* Monitored Assets - Collapsible */}
                    <div className={`${isNodesOpen ? 'lg:col-span-4 border-r border-white/5' : 'lg:col-span-12 border-b border-white/5'} bg-white/[0.01] transition-all duration-300`}>
                        <div
                            className="flex justify-between items-center p-4 cursor-pointer hover:bg-white/5"
                            onClick={() => setIsNodesOpen(!isNodesOpen)}
                        >
                            <div className="flex items-center gap-3">
                                <Server className="w-4 h-4 text-white/30" />
                                <h3 className="text-xs font-mono tracking-[0.4em] text-white/30 uppercase">Node Diagnostics</h3>
                            </div>
                            <div className="flex items-center gap-4">
                                {isNodesOpen && (
                                    <div className="flex gap-1">
                                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
                                        <span className="text-[9px] font-mono text-cyan-500/70">ACTIVE_MONITORING</span>
                                    </div>
                                )}
                                {isNodesOpen ? <ChevronUp className="w-4 h-4 text-white/20" /> : <ChevronDown className="w-4 h-4 text-white/20" />}
                            </div>
                        </div>

                        {isNodesOpen && (
                            <div className="p-6 space-y-3 border-t border-white/5">
                                {[
                                    { name: 'Atlas Primary Server', status: 'ACTIVE', load: '12%', color: 'text-cyan-400' },
                                    { name: 'Altimeter Data Node', status: 'SYNCED', load: '04%', color: 'text-cyan-400' },
                                    { name: 'Matrix Logic Core', status: 'ONLINE', load: '42%', color: 'text-white/60' },
                                    { name: 'Encryption Bridge', status: 'ACTIVE', load: '01%', color: 'text-cyan-400' }
                                ].map((node, i) => (
                                    <div key={i} className="flex justify-between items-center p-3 bg-white/[0.03] rounded-xl border border-white/5 hover:bg-white/10 transition-all">
                                        <div className="flex items-center gap-4">
                                            <Server className="w-4 h-4 text-white/20" />
                                            <p className="text-sm text-white/80 font-medium">{node.name}</p>
                                        </div>
                                        <div className="text-right">
                                            <p className={`text-[10px] font-mono font-bold ${node.color}`}>{node.status}</p>
                                            <p className="text-[9px] text-white/20 font-mono">{node.load} UTIL</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Intelligence Pipeline - Collapsible */}
                    <div className={`${(isNodesOpen && isIntelligenceOpen) ? 'lg:col-span-8' : 'lg:col-span-12'} bg-white/[0.01] transition-all duration-300`}>
                        <div
                            className="flex justify-between items-center p-4 cursor-pointer hover:bg-white/5 border-b border-white/5"
                            onClick={() => setIsIntelligenceOpen(!isIntelligenceOpen)}
                        >
                            <div className="flex items-center gap-3">
                                <Zap className="w-4 h-4 text-cyan-400" />
                                <h3 className="text-xs font-mono tracking-[0.4em] text-white/30 uppercase">Intelligence Pipeline</h3>
                            </div>
                            <div className="flex items-center gap-4">
                                {isIntelligenceOpen && (
                                    <div className="flex gap-1">
                                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
                                        <span className="text-[9px] font-mono text-amber-500/70">DECRYPTING_STREAM</span>
                                    </div>
                                )}
                                {isIntelligenceOpen ? <ChevronUp className="w-4 h-4 text-white/20" /> : <ChevronDown className="w-4 h-4 text-white/20" />}
                            </div>
                        </div>

                        {isIntelligenceOpen && (
                            <div className="p-6 flex flex-col justify-center">
                                <div className="flex items-center gap-12 w-full px-8">
                                    <div className="text-center group cursor-pointer" onClick={() => onNavigate('email')}>
                                        <p className="hud-tech-label mb-2">Unread Packets</p>
                                        <h2 className="text-6xl font-mono font-medium text-white group-hover:text-cyan-400 transition-all">{stats.inbox_unread || 0}</h2>
                                        <div className="mt-4 p-3 bg-white/5 rounded-xl border border-white/10 inline-block">
                                            <Mail className="w-6 h-6 text-white/60" />
                                        </div>
                                    </div>
                                    <div className="h-32 w-[1px] bg-white/10" />
                                    <div className="flex-1 space-y-4">
                                        <div>
                                            <p className="text-2xl text-white font-medium tracking-[0.2em] uppercase">Intelligence Stream</p>
                                            <p className="text-xs text-white/30 font-mono mt-2 tracking-widest">Available Packets :: {stats.inbox_total || 0}</p>
                                        </div>
                                        <div className="pt-4 border-t border-white/5">
                                            <div className="flex items-center gap-3">
                                                <div className="w-2 h-2 bg-amber-500 rounded-full animate-ping" />
                                                <p className="text-[10px] text-amber-500/80 font-mono uppercase tracking-[0.2em]">ALERT :: New intelligence detected in Sector 4</p>
                                            </div>
                                            <button onClick={() => onNavigate('email')} className="mt-4 text-[10px] text-white/40 hover:text-cyan-400 font-mono flex items-center gap-2 underline underline-offset-8 transition-colors">DECRYPT_STREAM_PROTOCOL &gt;</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Unified Mission Stream - Linearized Grid */}
                <div className="bg-white/5 border border-white/10 rounded-3xl overflow-hidden shadow-2xl">
                    <div className="bg-white/[0.02] p-6 border-b border-white/10 flex flex-col md:flex-row justify-between items-center gap-4">
                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-4 cursor-pointer group" onClick={() => setIsMissionFlowOpen(!isMissionFlowOpen)}>
                                <div className={`p-2 rounded-lg ${isMissionFlowOpen ? 'bg-cyan-500/20 text-cyan-400' : 'bg-white/5 text-white/30'} transition-all`}>
                                    <Calendar className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-medium text-white tracking-[0.2em] uppercase">Mission Flow</h3>
                                    <p className="text-[10px] font-mono text-white/20 tracking-[0.4em] uppercase">Unified Operational Interface</p>
                                </div>
                                {isMissionFlowOpen ? <ChevronUp className="w-5 h-5 text-white/20 ml-2" /> : <ChevronDown className="w-5 h-5 text-white/20 ml-2" />}
                            </div>
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="flex gap-2">
                                <button
                                    onClick={() => onNavigate('tasks')}
                                    className="px-6 py-2 bg-white/5 border border-white/5 rounded-xl text-xs font-mono text-white/40 hover:bg-white/10 hover:text-cyan-400 transition-all flex items-center gap-2"
                                >
                                    <ListTodo className="w-4 h-4" /> TASKS
                                </button>
                                <button
                                    onClick={() => onNavigate('calendar_google')}
                                    className="px-6 py-2 bg-white/5 border border-white/5 rounded-xl text-xs font-mono text-white/40 hover:bg-white/10 hover:text-cyan-400 transition-all flex items-center gap-2"
                                >
                                    <Calendar className="w-4 h-4" /> CALENDAR
                                </button>
                            </div>
                            <div className="h-8 w-[1px] bg-white/10 mx-2" />
                            <div className="px-5 py-2 bg-white/5 rounded-xl border border-white/5 flex items-center gap-4">
                                <span className="text-xs font-mono text-white/30 uppercase">Active Modules ::</span>
                                <span className="text-lg font-mono text-cyan-400">{schedule.length}</span>
                            </div>
                        </div>
                    </div>

                    {isMissionFlowOpen && (
                        <div className="p-10 bg-white/[0.01] backdrop-blur-sm">
                            {/* Foreman Protocol: Active Mission Briefing */}
                            <AnimatePresence mode="wait">
                                {activeBriefing ? (
                                    <_motion.div
                                        key="briefing"
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -20 }}
                                        className="mb-8"
                                    >
                                        <MissionBriefing
                                            phase={activeBriefing}
                                            onBack={() => setActiveBriefing(null)}
                                        />
                                    </_motion.div>
                                ) : (
                                    <_motion.div
                                        key="widgets"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="mb-8"
                                    >
                                        {/* The Oracle Protocol: Mission Intel Widget */}
                                        <MissionIntelWidget onLaunchBriefing={(phase) => setActiveBriefing(phase)} />
                                    </_motion.div>
                                )}
                            </AnimatePresence>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 max-h-[500px] overflow-y-auto custom-scrollbar">
                                {schedule.length === 0 ? (
                                    <div className="col-span-full py-16 text-center opacity-30">
                                        <p className="text-2xl font-mono tracking-widest uppercase mb-4">No Active Signals</p>
                                        <p className="text-sm font-mono tracking-widest">AWAITING SECTOR PROTOCOL ASSIGNMENT</p>
                                    </div>
                                ) : (
                                    schedule.map(item => (
                                        <MissionItem key={item.id} item={item} onNavigate={onNavigate} />
                                    ))
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Environmental Intelligence Row */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pb-8">
                    <div className="lg:col-span-9 bg-white/5 border border-white/10 rounded-3xl p-10 flex items-center gap-16 backdrop-blur-xl">
                        <div className="flex flex-col gap-3 min-w-[200px]">
                            <h3 className="hud-tech-label">Environmental Logic</h3>
                            <p className="text-4xl font-medium text-white tracking-[0.2em] uppercase leading-tight">Sector<br />Analysis</p>
                        </div>
                        <div className="flex-1 bg-white/[0.02] rounded-2xl p-6 border border-white/5 backdrop-blur-sm">
                            <WeatherForecast forecast={weather.forecast} loading={isWeatherLoading && !weather.forecast?.length} onRetry={() => { }} error={weather.error} />
                        </div>
                    </div>
                    <div className="lg:col-span-3 bg-white/5 border border-white/10 rounded-3xl p-10 relative overflow-hidden group">
                        <div className="matrix-overlay absolute inset-0 pointer-events-none opacity-20" />
                        <h3 className="hud-tech-label mb-6">Internal Diagnostics</h3>
                        <div className="space-y-3 relative z-10">
                            {[
                                { label: 'Secure Link', val: 'ESTABLISHED' },
                                { label: 'Data Stream', val: '4.2 GB/S' },
                                { label: 'Signal Ping', val: '12 MS' },
                                { label: 'Encryption', val: 'ENHANCED' }
                            ].map((d, i) => (
                                <div key={i} className="flex justify-between items-center text-xs font-mono">
                                    <span className="text-white/30 uppercase">{d.label}</span>
                                    <span className="text-cyan-400/80">{d.val}</span>
                                </div>
                            ))}
                            <div className="pt-6 mt-6 border-t border-white/5 flex items-center gap-3">
                                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
                                <span className="text-[10px] font-mono text-cyan-400/60 uppercase tracking-widest">Atlas Protocol V5.2</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <ChatBot onNavigate={onNavigate} />
            {toastElement}
        </div>
    );
};

export default Dashboard;
