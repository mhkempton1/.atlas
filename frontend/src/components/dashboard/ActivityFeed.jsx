import React, { useState, useEffect } from 'react';
import { Activity, Clock, Mail, FileText, Terminal, Shield } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';

const ActivityFeed = ({ showHeader = true }) => {
    const [activities, setActivities] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchActivity = async () => {
            try {
                const data = await SYSTEM_API.getActivityLog();
                setActivities(data.slice(0, 8)); // Show only recent 8
            } catch (err) {
                console.error("Failed to fetch activity", err);
            } finally {
                setLoading(false);
            }
        };
        fetchActivity();

        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchActivity, 30000);
        return () => clearInterval(interval);
    }, []);

    const getIcon = (type) => {
        switch (type) {
            case 'email': return <Mail className="w-3 h-3 text-purple-400" />;
            case 'doc': return <FileText className="w-3 h-3 text-blue-400" />;
            case 'calendar': return <Clock className="w-3 h-3 text-pink-400" />;
            case 'system': return <Terminal className="w-3 h-3 text-emerald-400" />;
            case 'security': return <Shield className="w-3 h-3 text-amber-400" />;
            default: return <Activity className="w-3 h-3 text-gray-400" />;
        }
    };

    if (loading) {
        return (
            <div className={`${showHeader ? 'bg-slate-800/50 border border-white/5 rounded-2xl p-6' : 'p-6'}`}>
                {showHeader && (
                    <div className="flex items-center gap-2 mb-4">
                        <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Live Activity</h3>
                    </div>
                )}
                <div className="text-center text-gray-600 text-sm py-8">Loading feed...</div>
            </div>
        );
    }

    return (
        <div className={`${showHeader ? 'bg-slate-800/50 border border-white/5 rounded-2xl overflow-hidden' : ''}`}>
            {showHeader && (
                <div className="bg-slate-900/50 p-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Live Activity</h3>
                    </div>
                    <div className="text-[9px] font-mono text-gray-600">REAL-TIME FEED</div>
                </div>
            )}

            <div className="p-4 space-y-2 max-h-[400px] overflow-y-auto custom-scrollbar">
                {activities.length === 0 ? (
                    <div className="text-center text-gray-600 text-sm py-8">No recent activity</div>
                ) : (
                    activities.map((item, idx) => (
                        <div
                            key={item.id || idx}
                            className="flex items-start gap-3 p-2 rounded-lg hover:bg-slate-900/30 transition-colors"
                        >
                            <div className="flex-shrink-0 p-1.5 rounded-md bg-slate-950/50">
                                {getIcon(item.type)}
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-start justify-between gap-2">
                                    <p className="text-xs font-medium text-gray-300 truncate">{item.action}</p>
                                    <span className="text-[9px] font-mono text-gray-600 flex-shrink-0">
                                        {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>
                                {item.target && (
                                    <p className="text-[10px] text-gray-500 truncate mt-0.5">{item.target}</p>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ActivityFeed;
