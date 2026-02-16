import React, { useState, useEffect } from 'react';
import { Layout, Calendar, CheckSquare, Mail, AlertTriangle, CloudSun, Briefcase, ChevronRight } from 'lucide-react';
import api from '../services/api';
import { PageHeader, Spinner, Section, Card } from './shared/UIComponents';

const MyDayDashboard = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboard = async () => {
            try {
                const res = await api.get('/dashboard/my-day');
                setData(res.data);
            } catch (err) {
                console.error("Dashboard failed", err);
            } finally {
                setLoading(false);
            }
        };
        fetchDashboard();
    }, []);

    if (loading) return <Spinner label="Analyzing your day..." />;
    if (!data) return <div>Failed to load dashboard.</div>;

    return (
        <div className="p-6 space-y-6 animate-fade-in pb-20">
            <PageHeader
                icon={Briefcase}
                title="Mission Control"
                subtitle={`Executive Summary for ${new Date(data.date).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}`}
            />

            {/* Weather Alert */}
            {data.weather && (
                <div className={`p-4 rounded-xl border flex items-center gap-4 ${data.weather.condition?.toLowerCase().includes('rain') || data.weather.condition?.toLowerCase().includes('storm')
                        ? 'bg-orange-500/10 border-orange-500/20 text-orange-400'
                        : 'bg-blue-500/10 border-blue-500/20 text-blue-400'
                    }`}>
                    <CloudSun className="w-6 h-6" />
                    <div>
                        <p className="text-sm font-bold">Weather Intel: {data.weather.condition} ({data.weather.temperature}°F)</p>
                        <p className="text-xs opacity-80">{data.weather.forecast || 'Check site safety protocols if conditions worsen.'}</p>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* 1. Critical Actions (High Urgency Emails) */}
                <Section title="Critical Intel" icon={AlertTriangle} badge={data.urgent_emails?.length}>
                    <div className="space-y-3">
                        {data.urgent_emails?.length === 0 ? (
                            <p className="text-xs text-gray-500 italic">No critical emails requiring immediate action.</p>
                        ) : (
                            data.urgent_emails.map(email => (
                                <Card key={email.email_id} className="border-l-4 border-l-red-500 bg-red-500/5">
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="text-[10px] font-bold text-red-400 uppercase">High Urgency</span>
                                        <span className="text-[10px] text-gray-500">{email.from_name}</span>
                                    </div>
                                    <h5 className="text-sm font-medium text-white truncate">{email.subject}</h5>
                                    <button className="mt-2 text-[10px] text-purple-400 font-bold flex items-center gap-1 hover:underline">
                                        Open Thread <ChevronRight className="w-3 h-3" />
                                    </button>
                                </Card>
                            ))
                        )}
                    </div>
                </Section>

                {/* 2. Outstanding Tasks (Due Today) */}
                <Section title="Primary Objectives" icon={CheckSquare} badge={data.tasks?.length}>
                    <div className="space-y-3">
                        {data.tasks?.length === 0 ? (
                            <p className="text-xs text-gray-500 italic">Zero objectives outstanding for today.</p>
                        ) : (
                            data.tasks.map(task => (
                                <Card key={task.task_id} className="hover:border-white/20 transition-colors">
                                    <div className="flex items-start gap-3">
                                        <div className={`mt-1 w-2 h-2 rounded-full ${task.priority === 'High' ? 'bg-red-500' : 'bg-emerald-500'}`} />
                                        <div className="flex-1">
                                            <h5 className="text-sm text-gray-200">{task.title}</h5>
                                            <p className="text-[10px] text-gray-500 mt-1">Status: {task.status || 'Active'}</p>
                                        </div>
                                    </div>
                                </Card>
                            ))
                        )}
                    </div>
                </Section>

                {/* 3. Schedule (Next 24h) */}
                <Section title="Deployment Schedule" icon={Calendar} badge={data.upcoming_events?.length}>
                    <div className="space-y-3">
                        {data.upcoming_events?.length === 0 ? (
                            <p className="text-xs text-gray-500 italic">Clear schedule for the next 24 hours.</p>
                        ) : (
                            data.upcoming_events.map(event => (
                                <Card key={event.event_id} className="bg-white/5">
                                    <div className="flex justify-between items-start">
                                        <div className="text-xs font-bold text-purple-400">
                                            {new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                        {event.location && <span className="text-[10px] text-gray-500">{event.location}</span>}
                                    </div>
                                    <h5 className="text-sm text-gray-300 mt-1">{event.summary || event.title}</h5>
                                </Card>
                            ))
                        )}
                    </div>
                </Section>

            </div>
        </div>
    );
};

export default MyDayDashboard;
