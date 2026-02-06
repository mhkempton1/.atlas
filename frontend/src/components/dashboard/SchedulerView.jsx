import React, { useState, useEffect } from 'react';
import { Calendar, Briefcase, Clock, AlertTriangle, Users } from 'lucide-react';
import { PageHeader, Section, Spinner, EmptyState, StatusBadge } from '../shared/UIComponents';

const SchedulerView = () => {
    const [schedule, setSchedule] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Use consistent API base
        const scheduleUrl = 'http://127.0.0.1:4201/api/v1/dashboard/schedule';

        fetch(scheduleUrl)
            .then(res => {
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                return res.json();
            })
            .then(data => {
                // Handle different date formats safely
                const sorted = data.sort((a, b) => {
                    if (a.current_start === "No Deadline") return 1;
                    if (b.current_start === "No Deadline") return -1;
                    return new Date(a.current_start) - new Date(b.current_start);
                });
                setSchedule(sorted);
                setLoading(false);
            })
            .catch(err => {
                console.error("Schedule Fetch Failed", err);
                setSchedule([]);
                setLoading(false);
            });
    }, []);

    if (loading) return <Spinner label="Loading Human Resources Data..." />;

    const priorityItems = schedule.filter(i => i.status === 'Prioritized' || i.status === 'In Progress').slice(0, 2);
    const upcomingItems = schedule.filter(i => !priorityItems.includes(i));

    return (
        <div className="h-full flex flex-col space-y-6 animate-slide-in">
            <PageHeader
                icon={Users}
                title="Human Resources & Scheduling"
                subtitle="Workforce Management"
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full overflow-hidden">
                {/* Left Column: Schedule */}
                <div className="lg:col-span-2 flex flex-col gap-6 overflow-y-auto pr-2">
                    {/* Priority Section */}
                    {priorityItems.length > 0 && (
                        <Section title="Priority Actions">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {priorityItems.map((item, idx) => (
                                    <div key={item.id || idx} className="bg-white/[0.03] border border-purple-500/20 rounded-xl p-4 relative overflow-hidden group backdrop-blur-xl">
                                        <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                                            <AlertTriangle className="w-16 h-16 text-primary" />
                                        </div>
                                        <div className="flex justify-between items-start mb-4 relative z-10">
                                            <h3 className="font-bold text-white text-lg">{item.name}</h3>
                                            <StatusBadge status={item.status} />
                                        </div>
                                        <div className="space-y-3 relative z-10">
                                            <div className="flex items-center gap-2 text-sm text-gray-400">
                                                <Briefcase className="w-4 h-4 text-purple-400" />
                                                <span>{item.project_id}</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-sm text-emerald-400">
                                                <Clock className="w-4 h-4" />
                                                <span>{item.current_start} (Active)</span>
                                            </div>
                                        </div>
                                        <div className={`mt-4 text-xs p-2 rounded border inline-block font-mono ${item.engineering_status === 'Approved'
                                            ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                                            : 'text-amber-400 bg-amber-500/10 border-amber-500/20'
                                            }`}>
                                            Engineering: {item.engineering_status}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Section>
                    )}

                    {/* Upcoming Section */}
                    <Section title="Upcoming Schedule">
                        {upcomingItems.length === 0 ? (
                            <EmptyState
                                icon={Calendar}
                                title="No Scheduled Items"
                                message="The schedule is currently clear."
                            />
                        ) : (
                            <div className="space-y-3">
                                {upcomingItems.map((item, idx) => (
                                    <div key={item.id || idx} className="flex items-center justify-between p-4 bg-white/[0.02] border border-white/5 rounded-lg hover:border-purple-500/30 transition-colors backdrop-blur-sm">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                {item.type === 'calendar' && <Calendar className="w-3 h-3 text-emerald-400" />}
                                                <h4 className="font-semibold text-gray-200">{item.name}</h4>
                                            </div>
                                            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                                                <span className="flex items-center gap-1"><Briefcase className="w-3 h-3" /> {item.project_id}</span>
                                                <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {item.current_start}</span>
                                            </div>
                                        </div>
                                        <StatusBadge status={item.status} />
                                    </div>
                                ))}
                            </div>
                        )}
                    </Section>
                </div>

                {/* Right Column: Personnel */}
                <div className="bg-white/[0.03] border border-white/5 rounded-xl ml-1 flex flex-col h-full overflow-hidden backdrop-blur-xl shadow-2xl">
                    <div className="p-4 border-b border-white/5 flex justify-between items-center">
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Personnel Directory</h3>
                        <span className="text-[10px] bg-white/5 text-gray-400 px-2 py-1 rounded">3 Online</span>
                    </div>

                    <div className="p-4">
                        <input className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-purple-500/50" placeholder="Search directory..." />
                    </div>

                    <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-1">
                        {[
                            { name: "Michael Kempton", role: "Administrator", status: "online" },
                            { name: "Sarah Connor", role: "Sec. Ops", status: "away" },
                            { name: "John Smith", role: "Engineering", status: "online" },
                            { name: "Alice Johnson", role: "Design", status: "offline" },
                            { name: "David Kim", role: "Analyst", status: "online" },
                        ].map((person, i) => (
                            <div key={i} className="flex items-center gap-3 p-2 rounded hover:bg-white/5 cursor-pointer transition-colors group">
                                <div className={`w-2 h-2 rounded-full ${person.status === 'online' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' :
                                    person.status === 'away' ? 'bg-amber-500' : 'bg-slate-700'
                                    }`} />
                                <div className="flex-1">
                                    <div className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">{person.name}</div>
                                    <div className="text-[10px] text-gray-500 uppercase tracking-wider">{person.role}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SchedulerView;
