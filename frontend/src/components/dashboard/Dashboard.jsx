import React, { useState, useEffect } from 'react';
import {
    Mail, FileText, Settings, Shield, Clock, Activity, LayoutDashboard,
    Server, ListTodo, Calendar, Zap, AlertTriangle, CheckCircle,
    BookOpen, Sun, Cloud, CloudRain, Wind, ChevronDown, ChevronUp,
    MessageSquare, Send, X, ExternalLink, ArrowDown, History as HistoryIcon,
    CheckSquare, Menu
} from 'lucide-react';
import { SYSTEM_API } from '../../services/api';
import { PageHeader, Section, Spinner, EmptyState } from '../shared/UIComponents';
import { useToast } from '../../hooks/useToast';
import { motion as _motion, AnimatePresence } from 'framer-motion';

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
    const isHealthy = healthPercentage >= 90;

    return (
        <div className="w-full flex items-center justify-between px-8 py-2 border-b border-white/5 bg-white/[0.01] backdrop-blur-md text-[10px] font-mono tracking-[0.25em] text-white/40 mb-1">
            <div className="flex items-center gap-16">
                <div className="flex items-center gap-4">
                    <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-cyan-500 animate-pulse' : 'bg-amber-500'}`} />
                    <span className="text-white/70 uppercase">System Status ::</span>
                    <span className={`${isHealthy ? 'text-cyan-400' : 'text-amber-400'} font-black`}>{isHealthy ? `NOMINAL (${healthPercentage}%)` : `DEGRADED (${healthPercentage}%)`}</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="opacity-40 uppercase">Sector Location ::</span>
                    <span className="text-white/60">{Math.abs(lat).toFixed(2)}° {lat >= 0 ? 'N' : 'S'} / {Math.abs(lon).toFixed(2)}° {lon >= 0 ? 'E' : 'W'}</span>
                </div>
            </div>

            <div className="flex items-center gap-16">
                <div className="flex items-center gap-2">
                    <span className="opacity-40 uppercase">Subsystem Flux ::</span>
                    <span className="text-cyan-400/80">98.4% STABLE</span>
                </div>
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
            className={`relative p-4 cursor-pointer hover:bg-white/5 transition-all group border-l-2 ${borderClass} bg-transparent flex items-center gap-4 border-y border-r border-white/5 rounded-xl shadow-lg w-full text-left`}
        >
            <div className={`p-2 rounded-lg bg-white/[0.05] border border-white/10 group-hover:border-primary/50 transition-colors ${color}`}>
                <Icon className="w-5 h-5" />
            </div>

            <div className="flex-1 min-w-0">
                <div className="flex justify-between items-baseline">
                    <h3 className="text-xl font-mono font-medium text-white tracking-tight leading-none">{value}</h3>
                </div>
                <p className="text-[9px] text-white/50 uppercase tracking-[0.2em] font-medium mt-1 truncate">{label}</p>
            </div>
        </button>
    );
});


const WeatherForecast = React.memo(({ forecast, loading, onRetry, error }) => {
    const scrollRef = React.useRef(null);
    const [isDown, setIsDown] = React.useState(false);
    const [startX, setStartX] = React.useState(0);
    const [scrollLeft, setScrollLeft] = React.useState(0);

    const handleMouseDown = (e) => {
        setIsDown(true);
        setStartX(e.pageX - scrollRef.current.offsetLeft);
        setScrollLeft(scrollRef.current.scrollLeft);
    };

    const handleMouseLeave = () => setIsDown(false);
    const handleMouseUp = () => setIsDown(false);

    const handleMouseMove = (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - scrollRef.current.offsetLeft;
        const walk = (x - startX) * 2;
        scrollRef.current.scrollLeft = scrollLeft - walk;
    };

    // Only show skeletons if we have NO data AND NO ERROR.
    if (loading && (!forecast || forecast.length === 0) && !error) {
        return (
            <div className="flex gap-4 pb-4 overflow-x-hidden opacity-50">
                {[...Array(7)].map((_, i) => (
                    <div key={i} className="flex-none w-[180px] bg-white/[0.02] border border-white/5 rounded-xl p-6 text-center animate-pulse">
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
        <div
            ref={scrollRef}
            onMouseDown={handleMouseDown}
            onMouseLeave={handleMouseLeave}
            onMouseUp={handleMouseUp}
            onMouseMove={handleMouseMove}
            className={`flex overflow-x-auto gap-4 pb-4 snap-x snap-mandatory no-scrollbar transition-all duration-500 -mx-4 px-4 sm:mx-0 sm:px-0 ${isDown ? 'cursor-grabbing select-none' : 'cursor-grab'}`}
        >
            {forecast.map((day, i) => (
                <div key={i} className="flex-none w-[200px] snap-center bg-transparent border border-white/10 rounded-xl p-6 text-center hover:bg-white/[0.05] transition-all group scale-95 hover:scale-100">
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

const MissionItem = ({ item, onNavigate }) => {
    const isTask = item.type === 'task';
    const isAltimeter = item.type === 'altimeter';

    return (
        <button
            onClick={() => onNavigate(isTask ? 'tasks' : isAltimeter ? 'projects' : 'calendar_google')}
            className={`p-4 bg-transparent border border-white/5 rounded-xl hover:bg-white/5 hover:border-cyan-500/30 transition-all cursor-pointer group flex items-center justify-between gap-4 w-full text-left`}
        >
            <div className="flex items-center gap-4">
                <div className={`p-2.5 rounded-lg ${isTask ? 'bg-amber-500/10 text-amber-500' : isAltimeter ? 'bg-cyan-500/10 text-cyan-400' : 'bg-purple-500/10 text-purple-400'}`}>
                    {isTask ? <CheckSquare className="w-5 h-5" /> : isAltimeter ? <Shield className="w-5 h-5" /> : <Clock className="w-5 h-5" />}
                </div>
                <div>
                    <h4 className="text-sm font-medium text-white group-hover:text-cyan-400 transition-colors leading-tight">{item.name}</h4>
                    <p className="text-[9px] font-mono text-white/30 uppercase mt-1">{isTask ? `Sector :: ${item.project_id || 'Core'}` : isAltimeter ? 'Altimeter Sync' : `Start :: ${item.current_start}`}</p>
                </div>
            </div>

            <div className="text-right">
                <span className={`text-[9px] font-mono px-2 py-0.5 rounded border ${isTask ? (item.deviation > 0 ? 'border-amber-500/40 text-amber-500' : 'border-cyan-500/20 text-cyan-500') : 'border-purple-500/20 text-purple-500'}`}>
                    {isTask ? (item.deviation > 0 ? `SLIPPAGE :: +${item.deviation}D` : 'OPTIMAL') : isAltimeter ? 'MILESTONE' : 'TEMPORAL'}
                </span>
                <p className="text-[9px] font-mono text-white/20 mt-1">{item.current_start}</p>
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
            setMessages(prev => [...prev, { role: 'bot', text: res.reply, links: res.links }]);
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
                        exit={{ opacity: 0, scale: 0.9, y: 0 }}
                        className="bg-slate-950/80 backdrop-blur-2xl border border-white/10 w-96 h-[550px] rounded-3xl shadow-[0_0_50px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden mb-6"
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
    const [loading, setLoading] = useState(!localStorage.getItem('dashboard_stats'));
    const [stats, setStats] = useState(() => JSON.parse(localStorage.getItem('dashboard_stats')) || {});
    const [healthDetails, setHealthDetails] = useState(() => JSON.parse(localStorage.getItem('system_health')) || { status: 'online' });
    const [weather, setWeather] = useState(() => JSON.parse(localStorage.getItem('weather_telemetry')) || { location: 'Analyzing...', forecast: [], source: 'Pending...', updated_at: '--:--' });
    const [weatherLoading, setWeatherLoading] = useState(!localStorage.getItem('weather_telemetry'));
    const [schedule, setSchedule] = useState(() => JSON.parse(localStorage.getItem('unified_schedule')) || []);
    const [isNodesOpen, setIsNodesOpen] = useState(false);
    const [isMissionFlowOpen, setIsMissionFlowOpen] = useState(() => JSON.parse(localStorage.getItem('dash_mission_open')) ?? true);
    const [isIntelligenceOpen, setIsIntelligenceOpen] = useState(true);

    const [coordinates, setCoordinates] = useState({ lat: 37.04, lon: -93.29 }); // Default Nixa, MO
    const [retryWeather, setRetryWeather] = useState(0);

    useEffect(() => {
        const loadCoreData = async () => {
            try {
                const [dashStats, scheduleData] = await Promise.all([
                    SYSTEM_API.getDashboardStats().catch(() => ({})),
                    SYSTEM_API.getUnifiedSchedule().catch(() => [])
                ]);
                setStats(dashStats);
                setSchedule(scheduleData);

                // Cache the fresh data
                localStorage.setItem('dashboard_stats', JSON.stringify(dashStats));
                if (dashStats.health) localStorage.setItem('system_health', JSON.stringify(dashStats.health));
                localStorage.setItem('unified_schedule', JSON.stringify(scheduleData));

            } catch (err) {
                console.error("Dashboard error", err);
            } finally {
                setLoading(false);
            }
        };

        const fetchWeather = async (lat = 37.04, lon = -93.29) => {
            setWeatherLoading(true);
            try {
                const weatherData = await SYSTEM_API.getWeather(lat, lon);
                if (weatherData.error) {
                    setWeather(prev => ({ ...prev, error: weatherData.error }));
                } else if (weatherData && Array.isArray(weatherData.forecast) && weatherData.forecast.length > 0) {
                    setWeather({ ...weatherData, error: null });

                    localStorage.setItem('weather_telemetry', JSON.stringify(weatherData));
                }
            } catch (err) {
                console.error("Failed to fetch weather telemetry:", err);
                setWeather(prev => ({ ...prev, error: err.message }));
            } finally {
                setWeatherLoading(false);
            }
        };

        loadCoreData();

        // Fetch weather immediately with default coordinates
        fetchWeather(37.04, -93.29);

        // Then try geolocating to update it
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((pos) => {
                const newLat = pos.coords.latitude;
                const newLon = pos.coords.longitude;
                setCoordinates({ lat: newLat, lon: newLon });
                fetchWeather(newLat, newLon);
            }, (err) => {
                // Silently fail to default
            }, { timeout: 3000 });
        }
    }, [retryWeather]);

    if (loading) return <Spinner label="Waking up Ethereal Systems..." />;

    return (
        <div className="min-h-screen flex flex-col animate-slide-in relative overflow-hidden bg-transparent">
            <TelemetryBar healthDetails={globalHealth} weather={weather} coordinates={coordinates} />

            <div className="flex-1 px-8 py-4 flex flex-col space-y-6 max-w-7xl w-full mx-auto">
                {/* Header Strip */}
                <div className="flex justify-between items-center border-b border-white/5 pb-4">
                    <div>
                        <h1 className="text-3xl font-mono font-medium tracking-[0.2em] text-white">CONSOLE</h1>
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

                {/* Primary Intelligence Grid REMOVED per user request */}

                {/* Unified Mission Stream - Linearized Grid */}
                <div className="bg-transparent border border-white/10 rounded-3xl overflow-hidden shadow-2xl">
                    <div className="bg-transparent p-6 border-b border-white/10 flex flex-col md:flex-row justify-between items-center gap-4">
                        <div className="flex flex-1 items-center justify-between w-full">
                            <div className="flex items-center gap-4 cursor-pointer group" onClick={() => setIsMissionFlowOpen(!isMissionFlowOpen)}>
                                <div className={`p-2 rounded-lg ${isMissionFlowOpen ? 'bg-cyan-500/20 text-cyan-400' : 'bg-white/5 text-white/30'} transition-all`}>
                                    <Calendar className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-medium text-white tracking-[0.2em] uppercase">Mission Flow</h3>
                                    <p className="text-[10px] font-mono text-white/20 tracking-[0.4em] uppercase">OPERATIONAL INTERFACE</p>
                                </div>
                                {isMissionFlowOpen ? <ChevronUp className="w-5 h-5 text-white/20 ml-2" /> : <ChevronDown className="w-5 h-5 text-white/20 ml-2" />}
                            </div>

                            {/* Consolidated Stats in Banner */}
                            <div className="hidden md:flex items-center gap-8">
                                <div className="flex flex-col items-end cursor-pointer group/stat" onClick={() => onNavigate('alt_tasks')}>
                                    <span className="text-[10px] font-mono text-cyan-400/60 uppercase tracking-widest group-hover/stat:text-cyan-400 transition-colors">Projects</span>
                                    <span className="text-lg font-mono text-white leading-tight">{stats.active_projects || 0}</span>
                                </div>
                                <div className="flex flex-col items-end cursor-pointer group/stat" onClick={() => onNavigate('tasks')}>
                                    <span className="text-[10px] font-mono text-amber-400/60 uppercase tracking-widest group-hover/stat:text-amber-400 transition-colors">Pending</span>
                                    <span className="text-lg font-mono text-white leading-tight">{stats.pending_tasks || 0}</span>
                                </div>
                                <div className="flex flex-col items-end cursor-pointer group/stat" onClick={() => onNavigate('calendar_google')}>
                                    <span className="text-[10px] font-mono text-purple-400/60 uppercase tracking-widest group-hover/stat:text-purple-400 transition-colors">Events</span>
                                    <span className="text-lg font-mono text-white leading-tight">{stats.upcoming_events || 0}</span>
                                </div>
                                <div className="flex flex-col items-end cursor-pointer group/stat" onClick={() => onNavigate('email')}>
                                    <span className="text-[10px] font-mono text-emerald-400/60 uppercase tracking-widest group-hover/stat:text-emerald-400 transition-colors">Unread</span>
                                    <span className="text-lg font-mono text-white leading-tight">{stats.inbox_unread || 0}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {isMissionFlowOpen && (
                        <div className="p-8">
                            <div className="flex justify-between items-center mb-6">
                                <h4 className="text-[10px] font-mono text-cyan-400/60 uppercase tracking-[0.3em]">Operational Stream :: Unified Chronological Feed</h4>
                                <div className="flex gap-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                                        <span className="text-[9px] font-mono text-white/30 uppercase">Calendar</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                                        <span className="text-[9px] font-mono text-white/30 uppercase">Tasks</span>
                                    </div>
                                </div>
                            </div>

                            {schedule.length > 0 ? (
                                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                                    {schedule.map((item, idx) => (
                                        <MissionItem key={item.id || idx} item={item} onNavigate={onNavigate} />
                                    ))}
                                </div>
                            ) : (
                                <div className="py-12 text-center border border-dashed border-white/10 rounded-2xl">
                                    <p className="text-xs font-mono text-white/20 uppercase tracking-widest">No active mission data found in current temporal window.</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Bottom Stats & Weather - Expanded to Full Width */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    <div className="lg:col-span-12 bg-transparent border border-white/10 rounded-3xl p-10 relative overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                        <h3 className="hud-tech-label mb-6">Environmental Telemetry</h3>
                        <div className="relative z-10">
                            <WeatherForecast forecast={weather.forecast} loading={weatherLoading} onRetry={() => setRetryWeather(c => c + 1)} error={weather.error} />
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
