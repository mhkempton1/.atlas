import React, { useState } from 'react';
import { X, Calendar, Clock, MapPin, Users, AlignLeft, Send, Loader2 } from 'lucide-react';

const EventCompose = ({ onClose, onSave }) => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [location, setLocation] = useState('');
    const [startTime, setStartTime] = useState('');
    const [endTime, setEndTime] = useState('');
    const [isAllDay, setIsAllDay] = useState(false);
    const [attendees, setAttendees] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!title || !startTime || !endTime) return;

        setLoading(true);
        try {
            await onSave({
                title,
                description,
                location,
                start_time: startTime,
                end_time: endTime,
                all_day: isAllDay,
                attendees: attendees.split(',').map(a => a.trim()).filter(a => a)
            });
            onClose();
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
            <div className="w-full max-w-lg bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden animate-slide-in">
                <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/5">
                    <div className="flex items-center gap-3">
                        <Calendar className="w-5 h-5 text-purple-400" />
                        <h3 className="text-lg font-bold text-white uppercase tracking-wider">New Mission Event</h3>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    <div>
                        <label className="block text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1.5 ml-1">Title</label>
                        <input
                            autoFocus
                            required
                            type="text"
                            placeholder="Brief mission summary..."
                            className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-purple-500/50 transition-all"
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1.5 ml-1">Start Time</label>
                            <input
                                required
                                type="datetime-local"
                                className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500/50 transition-all [color-scheme:dark]"
                                value={startTime}
                                onChange={e => setStartTime(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1.5 ml-1">End Time</label>
                            <input
                                required
                                type="datetime-local"
                                className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500/50 transition-all [color-scheme:dark]"
                                value={endTime}
                                onChange={e => setEndTime(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1.5 ml-1">Location</label>
                        <div className="relative">
                            <MapPin className="absolute left-4 top-3.5 w-4 h-4 text-gray-500" />
                            <input
                                type="text"
                                placeholder="Remote / Hangar 4 / Sector 7..."
                                className="w-full bg-slate-800 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-purple-500/50 transition-all"
                                value={location}
                                onChange={e => setLocation(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1.5 ml-1">Description</label>
                        <textarea
                            rows={3}
                            placeholder="Detailed protocol notes..."
                            className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-purple-500/50 transition-all resize-none"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1.5 ml-1">Attendees (Comma separated emails)</label>
                        <div className="relative">
                            <Users className="absolute left-4 top-3.5 w-4 h-4 text-gray-500" />
                            <input
                                type="text"
                                placeholder="atlas@nexus.com, oracle@nexus.com..."
                                className="w-full bg-slate-800 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-purple-500/50 transition-all"
                                value={attendees}
                                onChange={e => setAttendees(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="pt-2">
                        <button
                            disabled={loading}
                            type="submit"
                            className="w-full py-4 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl shadow-lg shadow-purple-900/40 transition-all flex items-center justify-center gap-2 group disabled:opacity-50"
                        >
                            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />}
                            Log New Mission Event
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EventCompose;
