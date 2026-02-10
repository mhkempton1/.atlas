import React, { useState, useEffect, useCallback } from 'react';
import { SYSTEM_API } from '../../services/api';
import { PageHeader, Section, Spinner, EmptyState, StatusBadge } from '../shared/UIComponents';
import { useToast } from '../../hooks/useToast';
import { Calendar, Clock, MapPin, Users, RefreshCw, ChevronRight } from 'lucide-react';
import { AnimatePresence, motion as Motion } from 'framer-motion';

const CalendarModule = () => {
    const [events, setEvents] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSyncing, setIsSyncing] = useState(false);
    const [days, setDays] = useState(14);
    const { addToast, toastElement } = useToast();

    const loadEvents = useCallback(async () => {
        setIsLoading(true);
        try {
            const data = await SYSTEM_API.getCalendarEvents(days);
            setEvents(data);
        } catch (error) {
            console.error("Failed to load events", error);
            addToast("Failed to load calendar events", "error");
        } finally {
            setIsLoading(false);
        }
    }, [days, addToast]);

    useEffect(() => {
        loadEvents();
    }, [loadEvents]);

    const handleSync = async () => {
        setIsSyncing(true);
        try {
            const result = await SYSTEM_API.syncCalendar();
            addToast(`Synced ${result.synced_count} events`, "success");
            loadEvents();
        } catch (error) {
            console.error("Sync failed", error);
            addToast("Calendar sync failed", "error");
        } finally {
            setIsSyncing(false);
        }
    };

    // Group events by date
    const groupedEvents = events.reduce((acc, event) => {
        if (!event.start_time) return acc;
        const date = new Date(event.start_time).toLocaleDateString();
        if (!acc[date]) acc[date] = [];
        acc[date].push(event);
        return acc;
    }, {});

    const sortedDates = Object.keys(groupedEvents).sort((a, b) => new Date(a) - new Date(b));

    const formatDateHeader = (dateStr) => {
        const date = new Date(dateStr);
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        if (date.toLocaleDateString() === today.toLocaleDateString()) return `Today - ${date.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}`;
        if (date.toLocaleDateString() === tomorrow.toLocaleDateString()) return `Tomorrow - ${date.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}`;
        return date.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' });
    };

    const formatTime = (isoString) => {
        return new Date(isoString).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    };

    return (
        <div className="h-full flex flex-col space-y-6 animate-fade-in p-6">
            <PageHeader
                title="Calendar Intelligence"
                subtitle="Google Calendar Events & Schedule"
                icon={Calendar}
                actions={
                    <div className="flex items-center gap-3">
                        <div className="flex bg-slate-800 rounded-lg p-1 border border-white/10">
                            {[7, 14, 30].map(d => (
                                <button
                                    key={d}
                                    onClick={() => setDays(d)}
                                    className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${days === d ? 'bg-purple-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'
                                        }`}
                                >
                                    {d} Days
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={handleSync}
                            disabled={isSyncing}
                            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg border border-white/10 transition-all disabled:opacity-50"
                        >
                            <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
                            {isSyncing ? 'Syncing...' : 'Sync Now'}
                        </button>
                    </div>
                }
            />

            <div className="flex-1 overflow-y-auto space-y-8 pr-2 custom-scrollbar">
                {isLoading ? (
                    <div className="flex justify-center py-20">
                        <Spinner size="lg" />
                    </div>
                ) : events.length === 0 ? (
                    <EmptyState
                        icon={Calendar}
                        title="No Upcoming Events"
                        description="Your calendar is clear for the selected range. Sync to update."
                        action={{ label: "Sync Now", onClick: handleSync }}
                    />
                ) : (
                    sortedDates.map(date => (
                        <div key={date} className="space-y-3">
                            <h3 className="text-sm font-bold text-purple-400 uppercase tracking-wider sticky top-0 bg-slate-950/90 backdrop-blur-sm py-2 z-10">
                                {formatDateHeader(date)}
                            </h3>
                            <div className="grid gap-3">
                                {groupedEvents[date].map(event => (
                                    <div
                                        key={event.event_id}
                                        className="group bg-slate-900/50 hover:bg-slate-800 border border-white/5 hover:border-purple-500/30 rounded-xl p-4 transition-all duration-300 flex items-start gap-4"
                                    >
                                        {/* Time Column */}
                                        <div className="w-24 flex-shrink-0 flex flex-col items-center justify-center border-r border-white/5 pr-4">
                                            {event.all_day ? (
                                                <span className="text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-1 rounded">All Day</span>
                                            ) : (
                                                <>
                                                    <span className="text-sm font-bold text-white">{formatTime(event.start_time)}</span>
                                                    <span className="text-xs text-gray-500">{formatTime(event.end_time)}</span>
                                                </>
                                            )}
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex justify-between items-start mb-1">
                                                <h4 className="text-base font-semibold text-white truncate pr-2 group-hover:text-purple-300 transition-colors">
                                                    {event.title}
                                                </h4>
                                                <StatusBadge status={event.status || 'confirmed'} />
                                            </div>

                                            <div className="flex flex-wrap gap-4 mt-2">
                                                {event.location && (
                                                    <div className="flex items-center gap-1.5 text-xs text-gray-400">
                                                        <MapPin className="w-3.5 h-3.5" />
                                                        <span className="truncate max-w-[200px]">{event.location}</span>
                                                    </div>
                                                )}
                                                <div className="flex items-center gap-1.5 text-xs text-gray-400">
                                                    <Users className="w-3.5 h-3.5" />
                                                    <span>
                                                        {(() => {
                                                            try {
                                                                const attendees = JSON.parse(event.attendees || '[]');
                                                                return `${attendees.length} Attendees`;
                                                            } catch {
                                                                return 'Attendees info unavailable';
                                                            }
                                                        })()}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Action Bar */}
                                            <div className="mt-3 pt-3 border-t border-white/5 flex gap-2">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        // Placeholder for task creation logic
                                                        addToast("Task creation from event coming soon", "info");
                                                    }}
                                                    className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 px-2 py-1 rounded hover:bg-emerald-500/10 transition-colors"
                                                >
                                                    <CheckSquare className="w-3 h-3" /> Create Task
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))
                )}
            </div>
            {toastElement}
        </div>
    );
};

export default CalendarModule;
