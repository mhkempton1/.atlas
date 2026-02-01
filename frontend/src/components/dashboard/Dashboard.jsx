import React, { useState, useEffect } from 'react';
import {
    Mail, FileText, Settings, Clock, Activity, LayoutDashboard,
    ListTodo, Calendar, Zap, BookOpen, Sun, Cloud, CloudRain,
    ChevronDown, ChevronUp, MessageSquare, Send, X, ExternalLink, ArrowDown,
    CheckSquare
} from 'lucide-react';
import { SYSTEM_API } from '../../services/api';
import { PageHeader, Section, Spinner, EmptyState } from '../shared/UIComponents';
import { useToast } from '../../hooks/useToast';
import { motion as _motion, AnimatePresence } from 'framer-motion';
import ActivityFeed from './ActivityFeed';
import MissionIntelWidget from './MissionIntelWidget';

const StatCard = ({ label, value, sub, icon, onClick, trend, color = "text-white" }) => {
    const Icon = icon;
    return (
        <div
            onClick={onClick}
            className="bg-slate-800/50 border border-white/5 rounded-xl p-5 cursor-pointer hover:bg-slate-800 transition-all hover:border-purple-500/30 group"
        >
            <div className="flex justify-between items-start mb-2">
                <div className={`p-2 rounded-lg bg-slate-900 group-hover:bg-purple-500/20 transition-colors ${color}`}>
                    <Icon className="w-5 h-5" />
                </div>
                {trend && (
                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${trend === 'up' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                        }`}>
                        {trend === 'up' ? 'Online' : 'Issue'}
                    </span>
                )}
            </div>
            <div className="mt-2">
                <h3 className="text-2xl font-bold text-white mb-1">{value}</h3>
                <p className="text-xs text-gray-400 uppercase tracking-widest font-semibold">{label}</p>
                {sub && <p className="text-xs text-gray-500 mt-2">{sub}</p>}
            </div>
        </div>
    );
};

// Memoized Weather Component for Performance
const WeatherForecast = React.memo(({ forecast }) => {
    if (!forecast) return null;
    return (
        <div className="grid grid-cols-5 gap-3">
            {forecast.map((day, i) => (
                <div key={i} className="bg-slate-900/40 border border-white/5 rounded-lg p-3 text-center">
                    <p className="text-[10px] uppercase font-bold text-gray-500 mb-2">{day.display_date}</p>
                    <div className="flex justify-center mb-1">
                        {(day.condition.includes('Sunny') || day.condition.includes('Clear')) && <Sun className="w-6 h-6 text-yellow-500" />}
                        {day.condition.includes('Cloudy') && !day.condition.includes('Partly') && <Cloud className="w-6 h-6 text-gray-400" />}
                        {day.condition.includes('Partly') && <div className="relative"><Sun className="w-4 h-4 text-yellow-500 absolute -top-1 -right-1" /><Cloud className="w-6 h-6 text-gray-400" /></div>}
                        {day.condition.includes('Snow') && <CloudRain className="w-6 h-6 text-blue-300 animate-pulse" />}
                    </div>
                    <div className="text-sm font-bold text-white">{day.high}°<span className="text-gray-500 font-normal ml-1">{day.low}°</span></div>
                    {day.rain_chance > 0 && (
                        <div className="text-[10px] text-blue-400 font-mono mt-1">{day.rain_chance}% precip</div>
                    )}
                    <div className="flex items-center justify-center gap-1 mt-2 text-[10px] text-gray-400">
                        <ArrowDown className="w-3 h-3 animate-bounce" style={{ transform: 'rotate(0deg)' }} />
                        <span>{day.wind_speed}mph</span>
                    </div>
                </div>
            ))}
        </div>
    );
});

const TaskItem = ({ task }) => (
    <div className="flex items-start gap-4 p-3 bg-slate-800/30 border border-white/5 rounded-lg mb-2">
        <div className={`mt-1 w-2 h-2 rounded-full ${task.status === 'Prioritized' ? 'bg-red-500' : 'bg-blue-500 animate-pulse'}`} />
        <div className="flex-1 min-w-0">
            <div className="flex justify-between items-start">
                <p className="text-sm font-semibold text-gray-200 truncate">{task.name}</p>
                <span className={`text-[10px] font-mono ${task.deviation > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                    {task.deviation > 0 ? `+${task.deviation}d SLIP` : 'ON TRACK'}
                </span>
            </div>
            <div className="flex gap-4 mt-1 text-[9px] text-gray-500 font-mono">
                <span>CREATED: {task.created_at}</span>
                <span>ORIGINAL DUE: {task.original_due_date}</span>
                <span className="text-gray-400 uppercase">PROJECT: {task.project_id}</span>
            </div>
        </div>
    </div>
);

// Memoized ChatBot Component for Performance
const ChatBot = React.memo(({ onNavigate }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([{ role: 'bot', text: 'Identity confirmed. I am **Atlas Intelligence**, linked to our internal procedure library and communication archive. Ask me about policies, safety, or system status.' }]);
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
            setMessages(prev => [...prev, { role: 'bot', text: "I'm having trouble connecting to my knowledge core." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed bottom-6 right-6 z-[100]">
            <AnimatePresence>
                {isOpen && (
                    <_motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="bg-slate-900 border border-purple-500/30 w-80 h-[450px] rounded-2xl shadow-2xl flex flex-col overflow-hidden mb-4"
                    >
                        <div className="bg-purple-600 p-4 flex justify-between items-center bg-gradient-to-r from-purple-600 to-indigo-600">
                            <div className="flex items-center gap-2">
                                <Zap className="w-5 h-5 text-yellow-300" />
                                <span className="font-bold text-white tracking-widest text-sm">ATLAS CORE</span>
                            </div>
                            <button onClick={() => setIsOpen(false)}><X className="w-5 h-5 text-white/70 hover:text-white" /></button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                            {messages.map((m, i) => (
                                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-[85%] p-3 rounded-xl text-xs ${m.role === 'user' ? 'bg-purple-600 text-white' : 'bg-slate-800 text-gray-200'}`}>
                                        <div dangerouslySetInnerHTML={{ __html: m.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                                        {m.links && m.links.map((link, j) => (
                                            <button
                                                key={j}
                                                className="mt-2 flex items-center gap-1.5 p-2 bg-slate-950/50 rounded-lg text-[10px] text-purple-400 hover:text-purple-300 transition-colors block w-full text-left"
                                                onClick={() => {
                                                    onNavigate(link.moduleId, link.path ? { path: link.path } : {});
                                                    setIsOpen(false);
                                                }}
                                            >
                                                <ExternalLink className="w-3 h-3" />
                                                {link.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ))}
                            {loading && <div className="text-[10px] text-gray-500 animate-pulse">Atlas is thinking...</div>}
                        </div>
                        <div className="p-4 border-t border-white/5 bg-slate-950/50">
                            <div className="flex gap-2">
                                <input
                                    className="flex-1 bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500/50"
                                    placeholder="Ask for system details..."
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                />
                                <button onClick={handleSend} className="p-2 bg-purple-600 rounded-lg text-white"><Send className="w-4 h-4" /></button>
                            </div>
                        </div>
                    </_motion.div>
                )}
            </AnimatePresence>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-14 h-14 bg-purple-600 rounded-full shadow-lg shadow-purple-500/20 flex items-center justify-center hover:bg-purple-500 transition-all hover:scale-110 active:scale-95 border-2 border-white/20"
            >
                {isOpen ? <X className="w-6 h-6 text-white" /> : <MessageSquare className="w-6 h-6 text-white" />}
            </button>
        </div>
    );
});

const Dashboard = ({ onNavigate }) => {
    const { toastElement } = useToast();
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({});
    const [healthDetails, setHealthDetails] = useState(null);
    const [weather, setWeather] = useState({ location: 'Analyzing...', forecast: [], source: 'Pending...', updated_at: '--:--:--' });
    const [schedule, setSchedule] = useState([]);
    const [isTasksOpen, setIsTasksOpen] = useState(false); // Start collapsed
    const [isWeatherOpen, setIsWeatherOpen] = useState(true);
    const [isActivityOpen, setIsActivityOpen] = useState(true);

    useEffect(() => {
        const loadCoreData = async () => {
            try {
                const [dashStats, health, scheduleData] = await Promise.all([
                    SYSTEM_API.getDashboardStats().catch(() => ({})),
                    SYSTEM_API.checkHealth().catch(() => ({ status: 'offline' })),
                    SYSTEM_API.getUnifiedSchedule().catch(() => [])
                ]);

                setStats(dashStats);
                setHealthDetails(health);
                setSchedule(scheduleData);
            } catch (err) {
                console.error("Dashboard core load error", err);
            } finally {
                setLoading(false);
            }
        };

        const loadWeather = async () => {
            let weatherData = null;
            try {
                if (navigator.geolocation) {
                    const position = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, {
                            timeout: 3500,
                            maximumAge: 600000
                        });
                    }).catch(() => null);

                    if (position) {
                        weatherData = await SYSTEM_API.getWeather(position.coords.latitude, position.coords.longitude).catch(() => null);
                    } else {
                        weatherData = await SYSTEM_API.getWeather().catch(() => null);
                    }
                } else {
                    weatherData = await SYSTEM_API.getWeather().catch(() => null);
                }
                if (weatherData) setWeather(weatherData);
            } catch {
                // Weather is non-critical
            }
        };

        loadCoreData();
        loadWeather();
    }, []);

    if (loading) return <Spinner label="Initializing Management Interface..." />;

    return (
        <div className="h-full flex flex-col space-y-6 animate-slide-in">
            <PageHeader
                icon={LayoutDashboard}
                title="Personal Assistant"
                subtitle="Mission Protocol Unified Dashboard"
            >
                <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-2 text-[10px] font-mono ${healthDetails?.status === 'online' ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : 'text-red-400 bg-red-500/10 border-red-500/20'} px-3 py-1 rounded-full border`}>
                        <div className={`w-1.5 h-1.5 rounded-full ${healthDetails?.status === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                        {healthDetails?.status === 'online' ? 'SYSTEM OPERATIONAL' : 'DEGRADED'}
                    </div>

                    <div className="relative group">
                        <button className="p-1.5 bg-slate-800 border border-white/10 rounded-lg hover:bg-slate-700 transition-colors">
                            <Settings className="w-4 h-4 text-gray-400" />
                        </button>
                        <div className="absolute right-0 top-full mt-2 w-48 bg-slate-900 border border-white/10 rounded-xl shadow-xl p-2 hidden group-hover:block z-50">
                            <div className="text-[10px] uppercase font-bold text-gray-500 px-2 py-1 mb-1">Admin Tools</div>
                            <button onClick={() => onNavigate('docs')} className="w-full text-left px-2 py-2 text-xs text-gray-300 hover:bg-white/5 rounded-lg flex items-center gap-2">
                                <FileText className="w-3 h-3 text-amber-400" /> Document Control
                            </button>
                            <button onClick={() => onNavigate('config')} className="w-full text-left px-2 py-2 text-xs text-gray-300 hover:bg-white/5 rounded-lg flex items-center gap-2">
                                <Settings className="w-3 h-3 text-purple-400" /> System Config
                            </button>
                        </div>
                    </div>
                </div>
            </PageHeader>

            {/* Primary Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    label="Active Missions"
                    value={schedule.filter(s => s.type === 'task').length}
                    sub="Current high-priority tasks"
                    icon={ListTodo}
                    color="text-emerald-400"
                    trend="up"
                    onClick={() => onNavigate('tasks')}
                />
                <StatCard
                    label="Unread Intel"
                    value={stats.inbox_unread || 0}
                    sub="Communications pending review"
                    icon={Mail}
                    color="text-blue-400"
                    trend={stats.inbox_unread > 50 ? 'down' : 'up'}
                    onClick={() => onNavigate('email')}
                />
                <StatCard
                    label="Policy Library"
                    value={stats.knowledge_docs || 0}
                    sub="Total SOPs & Guidelines"
                    icon={BookOpen}
                    color="text-purple-400"
                    onClick={() => onNavigate('procedures')}
                />
                <StatCard
                    label="System Health"
                    value={healthDetails?.status === 'online' ? '100%' : '85%'}
                    sub="Integrated node status"
                    icon={Activity}
                    color={healthDetails?.status === 'online' ? 'text-emerald-400' : 'text-red-400'}
                    trend={healthDetails?.status === 'online' ? 'up' : 'down'}
                    onClick={() => onNavigate('history')}
                />
            </div>

            {/* STACKED FLOW (MOBILE ORIENTED) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left Column: Forecast & Inbox */}
                <div className="space-y-6">
                    {/* Weather Forecast */}
                    <div className="bg-slate-800/50 border border-white/5 rounded-2xl shadow-xl overflow-hidden">
                        <div
                            className="bg-slate-900/50 p-4 flex justify-between items-center cursor-pointer hover:bg-slate-900 transition-colors"
                            onClick={() => setIsWeatherOpen(!isWeatherOpen)}
                        >
                            <div className="flex items-center gap-2 text-xs font-bold text-blue-400 uppercase tracking-widest">
                                <Cloud className="w-4 h-4" />
                                5-Day Outlook
                            </div>
                            {isWeatherOpen ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
                        </div>
                        {isWeatherOpen && (
                            <div className="p-5 overflow-hidden">
                                <WeatherForecast forecast={weather.forecast} />
                                <div className="flex justify-between items-center mt-4 px-2">
                                    <p className="text-[9px] text-gray-600 uppercase tracking-tighter">Loc: {weather.location}</p>
                                    <p className="text-[9px] text-blue-500/60 font-mono italic">Source: {weather.source || 'Live Feed'}</p>
                                    <p className="text-[9px] text-gray-600 uppercase tracking-tighter">Sync: {weather.updated_at}</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Unified Inbox Access (Primary Call to Action) */}
                    <div
                        onClick={() => onNavigate('email')}
                        className="bg-gradient-to-br from-indigo-600 to-purple-600 rounded-2xl p-6 shadow-xl cursor-pointer hover:scale-[1.02] transition-transform active:scale-[0.98] relative overflow-hidden group"
                    >
                        <Mail className="w-20 h-20 text-white/10 absolute -right-4 -bottom-4 group-hover:scale-110 transition-transform" />
                        <div className="relative z-10 flex justify-between items-center">
                            <div>
                                <h2 className="text-3xl font-black text-white">{stats.inbox_unread || 0}</h2>
                                <p className="text-xs text-white/70 font-bold uppercase tracking-widest mt-1">Unread Intelligence</p>
                                <p className="text-[10px] text-white/50 mt-4">{stats.inbox_total || 0} TOTAL MESSAGES IN ARCHIVE</p>
                            </div>
                            <div className="p-3 bg-white/20 rounded-xl backdrop-blur-md">
                                <Mail className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </div>

                    {/* Activity Feed */}
                    <div className="bg-slate-800/50 border border-white/5 rounded-2xl shadow-xl overflow-hidden">
                        <div
                            className="bg-slate-900/50 p-4 flex justify-between items-center cursor-pointer hover:bg-slate-900 transition-colors"
                            onClick={() => setIsActivityOpen(!isActivityOpen)}
                        >
                            <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-widest">
                                <Activity className="w-4 h-4 animate-pulse" />
                                Live Activity
                            </div>
                            {isActivityOpen ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
                        </div>
                        {isActivityOpen && (
                            <ActivityFeed showHeader={false} />
                        )}
                    </div>
                </div>

                {/* Right Column: Schedule & Tasks (Spans 2 on desktop) */}
                <div className="lg:col-span-2 space-y-6">

                    {/* The Oracle Protocol: Mission Intel Widget */}
                    <MissionIntelWidget />

                    <div className="bg-slate-800/50 border border-white/5 rounded-2xl shadow-xl overflow-hidden">
                        <div
                            className="bg-slate-900/50 p-4 flex justify-between items-center cursor-pointer hover:bg-slate-900 transition-colors"
                            onClick={() => setIsTasksOpen(!isTasksOpen)}
                        >
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2">
                                    <Calendar className="w-4 h-4 text-emerald-400" />
                                    <span className="font-bold text-xs uppercase tracking-widest">Mission Tasks & Schedule</span>
                                    <span className="ml-2 px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded text-[9px] font-mono">
                                        {schedule.filter(s => s.type === 'task').length} ACTIVE
                                    </span>
                                </div>
                                <button
                                    onClick={(e) => { e.stopPropagation(); onNavigate('tasks'); }}
                                    className="p-1 hover:bg-emerald-500/20 rounded transition-colors"
                                    title="Add Mission Task"
                                >
                                    <Zap className="w-3.5 h-3.5 text-emerald-400" />
                                </button>
                                <div className="h-4 w-px bg-white/10" />
                                <button
                                    onClick={(e) => { e.stopPropagation(); onNavigate('calendar_google'); }}
                                    className="p-1 hover:bg-emerald-500/20 rounded transition-colors"
                                    title="Full Calendar"
                                >
                                    <Calendar className="w-3.5 h-3.5 text-emerald-400" />
                                </button>
                                <button
                                    onClick={(e) => { e.stopPropagation(); onNavigate('tasks'); }}
                                    className="p-1 hover:bg-emerald-500/20 rounded transition-colors"
                                    title="Task Management"
                                >
                                    <CheckSquare className="w-3.5 h-3.5 text-emerald-400" />
                                </button>
                            </div>
                            {isTasksOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </div>
                        {isTasksOpen && (
                            <div className="p-4 max-h-[350px] overflow-y-auto custom-scrollbar">
                                {schedule.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center py-10 opacity-30">
                                        <Zap className="w-8 h-8 mb-2" />
                                        <p className="text-[10px] font-bold uppercase tracking-widest">No Active Missions</p>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {schedule.map(item => (
                                            <div key={item.id}>
                                                {item.type === 'task' ? <TaskItem task={item} /> : (
                                                    <div className="flex gap-4 p-3 border-l-2 border-emerald-500 bg-emerald-500/5 mb-2 rounded-r-lg">
                                                        <Clock className="w-4 h-4 text-emerald-400 shrink-0" />
                                                        <div>
                                                            <p className="text-sm font-semibold text-gray-200">{item.name}</p>
                                                            <p className="text-[10px] text-emerald-400/70 font-mono mt-1 uppercase tracking-tighter">
                                                                EVENT @ {item.current_start}
                                                            </p>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                </div>
            </div>

            {/* Chat Bot Layer */}
            <ChatBot onNavigate={onNavigate} />

            {toastElement}
        </div>
    );
};

export default Dashboard;
