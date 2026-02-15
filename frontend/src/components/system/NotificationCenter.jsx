import React, { useState, useEffect, useRef } from 'react';
import { Bell, BellOff, X, ExternalLink, Trash2, Check, AlertCircle, Info, Calendar as CalendarIcon, ShieldCheck } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';
import { motion, AnimatePresence } from 'framer-motion';

const NotificationCenter = ({ notifications, onMarkRead, onClearAll }) => {
    const [isOpen, setIsOpen] = useState(false);
    const popoverRef = useRef(null);
    const unreadCount = notifications.filter(n => !n.is_read).length;

    const getIcon = (type) => {
        switch (type) {
            case 'health': return <AlertCircle className="w-4 h-4 text-red-400" />;
            case 'calendar': return <CalendarIcon className="w-4 h-4 text-purple-400" />;
            case 'task': return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
            case 'system': return <Info className="w-4 h-4 text-blue-400" />;
            default: return <Bell className="w-4 h-4 text-gray-400" />;
        }
    };

    return (
        <div className="relative" ref={popoverRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`relative p-2 rounded-xl border transition-all hover:bg-white/5 ${unreadCount > 0 ? 'border-amber-500/30 bg-amber-500/5' : 'border-white/10'}`}
            >
                <Bell className={`w-5 h-5 ${unreadCount > 0 ? 'text-amber-400 animate-pulse' : 'text-white/40'}`} />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-amber-500 text-black text-[10px] font-black rounded-full flex items-center justify-center border-2 border-black">
                        {unreadCount}
                    </span>
                )}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 10 }}
                        className="absolute right-0 mt-3 w-80 bg-black/60 backdrop-blur-3xl border border-white/10 rounded-2xl shadow-2xl z-[1000] overflow-hidden"
                    >
                        <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/5">
                            <h3 className="text-xs font-bold tracking-[0.2em] uppercase text-white/60">System Alerts</h3>
                            <div className="flex gap-2">
                                <button onClick={onClearAll} className="p-1 hover:text-red-400 transition-colors" title="Clear All">
                                    <Trash2 className="w-3.5 h-3.5" />
                                </button>
                                <button onClick={() => setIsOpen(false)} className="p-1 hover:text-white transition-colors">
                                    <X className="w-3.5 h-3.5" />
                                </button>
                            </div>
                        </div>

                        <div className="max-h-96 overflow-y-auto custom-scrollbar">
                            {notifications.length === 0 ? (
                                <div className="p-8 text-center">
                                    <BellOff className="w-8 h-8 text-white/10 mx-auto mb-3" />
                                    <p className="text-[10px] font-mono text-white/20 uppercase tracking-widest">No active alerts</p>
                                </div>
                            ) : (
                                notifications.map(notif => (
                                    <div
                                        key={notif.id}
                                        className={`p-4 border-b border-white/5 transition-all hover:bg-white/5 ${!notif.is_read ? 'bg-white/[0.02]' : 'opacity-60'}`}
                                    >
                                        <div className="flex justify-between items-start mb-1">
                                            <div className="flex items-center gap-2">
                                                {getIcon(notif.type)}
                                                <span className="text-[10px] font-mono font-bold uppercase tracking-tighter text-white/80">{notif.title}</span>
                                            </div>
                                            {!notif.is_read && (
                                                <button onClick={() => onMarkRead(notif.id)} className="text-cyan-400 hover:text-cyan-300">
                                                    <Check className="w-3.5 h-3.5" />
                                                </button>
                                            )}
                                        </div>
                                        <p className="text-xs text-white/50 mb-3 leading-relaxed">{notif.message}</p>
                                        <div className="flex justify-between items-end">
                                            <span className="text-[9px] font-mono text-white/20">{new Date(notif.created_at).toLocaleTimeString()}</span>
                                            {notif.link && (
                                                <button
                                                    onClick={() => {
                                                        const moduleId = notif.link.replace('/', '');
                                                        window.dispatchEvent(new CustomEvent('app-navigate', { detail: { moduleId } }));
                                                        setIsOpen(false);
                                                    }}
                                                    className="text-[9px] font-mono text-cyan-400/60 flex items-center gap-1 hover:text-cyan-300"
                                                >
                                                    NAVIGATE <ExternalLink className="w-2.5 h-2.5" />
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default NotificationCenter;
