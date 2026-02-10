import React, { useState, useEffect, useRef } from 'react';
import {
    Search, Command, X, ArrowRight, Zap,
    LayoutDashboard, BookOpen, Mail, ShieldCheck,
    Calendar, History, Settings, FileText
} from 'lucide-react';
import { motion as _motion, AnimatePresence } from 'framer-motion';
import { SYSTEM_API } from '../../services/api';

const CommandBar = ({ isOpen, onClose, onNavigate, modules }) => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const inputRef = useRef(null);

    // Filtered modules based on query
    const filteredModules = modules.filter(m =>
        m.label.toLowerCase().includes(query.toLowerCase()) ||
        m.id.toLowerCase().includes(query.toLowerCase())
    ).slice(0, 5);

    useEffect(() => {
        if (isOpen) {
            setQuery('');
            setSelectedIndex(0);
            setTimeout(() => inputRef.current?.focus(), 50);
        }
    }, [isOpen]);

    // Semantic Search Debounce
    useEffect(() => {
        if (!query.trim() || query.length < 3) {
            setResults([]);
            return;
        }

        const timeout = setTimeout(async () => {
            setIsLoading(true);
            try {
                const searchResults = await SYSTEM_API.searchKnowledge(query);
                setResults(searchResults.slice(0, 5));
            } catch (err) {
                console.error("Command search failed", err);
            } finally {
                setIsLoading(false);
            }
        }, 300);

        return () => clearTimeout(timeout);
    }, [query]);

    const handleKeyDown = (e) => {
        const totalItems = filteredModules.length + results.length;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => (prev + 1) % totalItems);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => (prev - 1 + totalItems) % totalItems);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            handleSelect();
        } else if (e.key === 'Escape') {
            onClose();
        }
    };

    const handleSelect = () => {
        if (selectedIndex < filteredModules.length) {
            const mod = filteredModules[selectedIndex];
            onNavigate(mod.id);
            onClose();
        } else {
            const res = results[selectedIndex - filteredModules.length];
            onNavigate('procedures', { path: res.metadata.path || res.metadata.full_path });
            onClose();
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] px-4 sm:px-6 md:px-8">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black/60 backdrop-blur-sm"
                    onClick={onClose}
                />

                <_motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -20, filter: 'blur(10px)' }}
                    animate={{ opacity: 1, scale: 1, y: 0, filter: 'blur(0px)' }}
                    exit={{ opacity: 0, scale: 0.95, y: -20, filter: 'blur(10px)' }}
                    className="bg-white/[0.02] backdrop-blur-2xl border border-white/10 w-full max-w-2xl rounded-2xl shadow-[0_0_50px_-12px_rgba(168,85,247,0.3)] overflow-hidden flex flex-col max-h-[80vh]"
                >
                    <div className="flex items-center gap-3 p-4 border-b border-white/5 bg-white/[0.02]">
                        <Command className="w-5 h-5 text-purple-400" />
                        <input
                            ref={inputRef}
                            type="text"
                            placeholder="Type a command or search documents..."
                            className="flex-1 bg-transparent border-none text-white focus:outline-none placeholder:text-slate-500 text-lg"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                        <div className="flex items-center gap-1.5 px-1.5 py-0.5 rounded border border-white/10 text-[10px] text-slate-400 font-mono">
                            ESC
                        </div>
                    </div>

                    <div className="max-h-[60vh] overflow-y-auto p-2 custom-scrollbar">
                        {/* Modules Suggestion */}
                        {filteredModules.length > 0 && (
                            <div className="mb-2">
                                <div className="px-3 py-1 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Modules</div>
                                {filteredModules.map((mod, idx) => (
                                    <div
                                        key={mod.id}
                                        onClick={() => { onNavigate(mod.id); onClose(); }}
                                        className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${selectedIndex === idx ? 'bg-purple-600/20 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <mod.icon className={`w-4 h-4 ${selectedIndex === idx ? 'text-purple-400' : 'text-slate-500'}`} />
                                            <span className="text-sm font-medium">{mod.label}</span>
                                        </div>
                                        {selectedIndex === idx && <ArrowRight className="w-4 h-4 text-purple-400 animate-pulse" />}
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Search Results */}
                        {results.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-white/5">
                                <div className="px-3 py-1 text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center justify-between">
                                    <span>Intelligence Base</span>
                                    {isLoading && <Zap className="w-3 h-3 animate-spin text-purple-400" />}
                                </div>
                                {results.map((res, idx) => {
                                    const globalIdx = filteredModules.length + idx;
                                    return (
                                        <div
                                            key={res.id}
                                            onClick={() => { onNavigate('procedures', { path: res.metadata.path }); onClose(); }}
                                            className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${selectedIndex === globalIdx ? 'bg-purple-600/20 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
                                        >
                                            <div className="flex items-center gap-3 overflow-hidden">
                                                <div className="p-1.5 rounded-md bg-white/5">
                                                    <FileText className="w-3.5 h-3.5 text-blue-400" />
                                                </div>
                                                <div className="overflow-hidden">
                                                    <div className="text-sm font-medium truncate">{res.metadata.title}</div>
                                                    <div className="text-[10px] text-slate-600 truncate">{res.content_snippet}</div>
                                                </div>
                                            </div>
                                            {selectedIndex === globalIdx && <ArrowRight className="w-4 h-4 text-purple-400 animate-pulse" />}
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {query && filteredModules.length === 0 && results.length === 0 && !isLoading && (
                            <div className="p-8 text-center text-slate-600 italic text-sm">
                                No commands or documents found for "{query}"
                            </div>
                        )}
                    </div>

                    <div className="p-3 border-t border-white/5 bg-white/[0.01] flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-1 text-[10px] text-slate-500 uppercase tracking-widest">
                                <span className="p-1 rounded bg-white/5 border border-white/10 font-mono">ENTER</span> to select
                            </div>
                            <div className="flex items-center gap-1 text-[10px] text-slate-500 uppercase tracking-widest">
                                <span className="p-1 rounded bg-white/5 border border-white/10 font-mono">↑↓</span> to navigate
                            </div>
                        </div>
                        <div className="text-[10px] font-mono text-purple-500/50">ATLAS COMMAND OS v1.2</div>
                    </div>
                </_motion.div>
            </div>
        </AnimatePresence>
    );
};

export default CommandBar;
