import React, { useState, useEffect } from 'react';
import { History, Clock, FileText, Mail, Terminal, Shield, Database, Activity, ChevronDown, ChevronRight } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';
import { PageHeader, Section, Spinner, EmptyState } from '../shared/UIComponents';

const HistoryItem = ({ item }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    const getIcon = (type) => {
        switch (type) {
            case 'email': return <Mail className="w-3.5 h-3.5 text-purple-400" />;
            case 'doc': return <FileText className="w-3.5 h-3.5 text-blue-400" />;
            case 'calendar': return <Clock className="w-3.5 h-3.5 text-pink-400" />;
            case 'system': return <Terminal className="w-3.5 h-3.5 text-emerald-400" />;
            case 'security': return <Shield className="w-3.5 h-3.5 text-amber-400" />;
            default: return <Activity className="w-3.5 h-3.5 text-gray-400" />;
        }
    };

    const timeStr = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    return (
        <div className="border-b border-white/5 last:border-0">
            <div
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-4 py-3 px-2 hover:bg-white/10 cursor-pointer transition-colors group"
            >
                <div className="flex-shrink-0 w-8 flex justify-center">
                    {getIcon(item.type)}
                </div>

                <div className="flex-shrink-0 w-20 text-[10px] font-mono text-gray-500 uppercase">
                    {timeStr}
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-gray-200 truncate">{item.action}</span>
                        <span className="text-xs text-gray-500 truncate">{item.target}</span>
                    </div>
                </div>

                <div className="flex-shrink-0 text-gray-600 group-hover:text-gray-400">
                    {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </div>
            </div>

            {isExpanded && item.details && (
                <div className="px-14 pb-4 animate-slide-down">
                    <div className="bg-white/[0.02] border border-white/5 rounded p-3 text-xs font-mono text-gray-400 leading-relaxed overflow-x-auto backdrop-blur-xl">
                        {item.details}
                    </div>
                </div>
            )}
        </div>
    );
};

const HistoryView = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const data = await SYSTEM_API.getActivityLog();
                setLogs(data);
            } catch (err) {
                console.error("Failed to fetch activity logs", err);
            } finally {
                setLoading(false);
            }
        };
        fetchLogs();
    }, []);

    // Grouping by Date
    const grouped = logs.reduce((acc, item) => {
        const dateKey = new Date(item.timestamp).toLocaleDateString([], {
            month: 'long',
            day: 'numeric',
            year: 'numeric'
        });

        // Handle "Today" and "Yesterday"
        const today = new Date().toLocaleDateString([], { month: 'long', day: 'numeric', year: 'numeric' });
        const yesterday = new Date(Date.now() - 86400000).toLocaleDateString([], { month: 'long', day: 'numeric', year: 'numeric' });

        const label = dateKey === today ? 'Today' : (dateKey === yesterday ? 'Yesterday' : dateKey);

        if (!acc[label]) acc[label] = [];
        acc[label].push(item);
        return acc;
    }, {});

    if (loading) return <Spinner label="Loading Audit Trail..." />;

    return (
        <div className="h-full flex flex-col space-y-6 animate-slide-in">
            <PageHeader
                icon={History}
                title="System Activity Log"
                subtitle="Real-time Audit Trail & Database Events"
            />

            {logs.length === 0 ? (
                <EmptyState
                    icon={Database}
                    title="No Activity Yet"
                    description="System events will appear here as they occur."
                />
            ) : (
                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                    {Object.keys(grouped).map(date => (
                        <div key={date} className="mb-8">
                            <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-4 px-2 flex items-center gap-3">
                                {date}
                                <div className="h-px bg-white/5 flex-1" />
                            </h3>
                            <div className="bg-white/[0.02] border border-white/5 rounded-xl overflow-hidden backdrop-blur-md">
                                {grouped[date].map(item => (
                                    <HistoryItem key={item.id} item={item} />
                                ))}
                            </div>
                        </div>
                    ))}

                    <div className="text-center py-8 opacity-50">
                        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 border border-white/5">
                            <Clock className="w-3 h-3 text-gray-500" />
                            <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">End of visible trail</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default HistoryView;
