import React, { useState, useEffect } from 'react';
import { SYSTEM_API } from '../../services/api';
import { CheckCircle, AlertTriangle, Clock, ArrowRight } from 'lucide-react';

const DailyDigestWidget = ({ onNavigate }) => {
    const [digest, setDigest] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDigest = async () => {
            try {
                const data = await SYSTEM_API.getDailyDigest();
                setDigest(data);
            } catch (err) {
                console.error("Failed to load daily digest", err);
            } finally {
                setLoading(false);
            }
        };
        fetchDigest();
    }, []);

    if (loading) return null;
    if (!digest) return null;

    const { due_today, overdue, completed_yesterday } = digest;

    // Helper to render task list
    const renderTaskList = (tasks, emptyMsg) => {
        if (!tasks || tasks.length === 0) {
            return <p className="text-xs text-white/30 italic">{emptyMsg}</p>;
        }
        return (
            <div className="space-y-2 mt-2">
                {tasks.slice(0, 3).map(task => (
                    <div key={task.task_id} className="flex justify-between items-center group cursor-pointer" onClick={() => onNavigate('tasks')}>
                        <span className="text-xs text-white/70 truncate group-hover:text-cyan-400 transition-colors">{task.title}</span>
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${task.priority === 'high' ? 'bg-red-500/20 text-red-400' : 'bg-white/10 text-white/40'}`}>
                            {task.priority?.toUpperCase()}
                        </span>
                    </div>
                ))}
                {tasks.length > 3 && (
                    <p className="text-[10px] text-white/30 mt-1 cursor-pointer hover:text-white" onClick={() => onNavigate('tasks')}>
                        + {tasks.length - 3} more
                    </p>
                )}
            </div>
        );
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 animate-slide-in">
            {/* Focus Today */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 backdrop-blur-md relative overflow-hidden">
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                        <Clock className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="text-sm font-medium text-white">Focus Today</h3>
                        <p className="text-[10px] text-white/40 font-mono uppercase tracking-wider">{due_today.length} TASKS DUE</p>
                    </div>
                </div>
                {renderTaskList(due_today, "No tasks due today.")}
            </div>

            {/* Attention Needed */}
            <div className={`bg-white/5 border rounded-xl p-4 backdrop-blur-md relative overflow-hidden ${overdue.length > 0 ? 'border-red-500/30' : 'border-white/10'}`}>
                <div className="flex items-center gap-3 mb-2">
                    <div className={`p-2 rounded-lg ${overdue.length > 0 ? 'bg-red-500/10 text-red-400' : 'bg-white/5 text-white/30'}`}>
                        <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="text-sm font-medium text-white">Attention Needed</h3>
                        <p className="text-[10px] text-white/40 font-mono uppercase tracking-wider">{overdue.length} OVERDUE</p>
                    </div>
                </div>
                {renderTaskList(overdue, "All caught up!")}
            </div>

            {/* Achievements */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 backdrop-blur-md relative overflow-hidden flex flex-col justify-center">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-lg bg-green-500/10 text-green-400">
                        <CheckCircle className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="text-sm font-medium text-white">Achievements</h3>
                        <p className="text-[10px] text-white/40 font-mono uppercase tracking-wider">COMPLETED YESTERDAY</p>
                    </div>
                </div>
                <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-mono text-white">{completed_yesterday.length}</span>
                    <span className="text-xs text-white/40 uppercase tracking-widest">Tasks</span>
                </div>
                <button
                    onClick={() => onNavigate('tasks')}
                    className="mt-4 flex items-center gap-2 text-[10px] font-mono text-white/40 hover:text-white transition-colors group"
                >
                    VIEW_HISTORY <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                </button>
            </div>
        </div>
    );
};

export default DailyDigestWidget;
