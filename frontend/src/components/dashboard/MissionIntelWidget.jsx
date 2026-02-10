import React, { useState, useEffect } from 'react';
import { Sparkles, FileText, CloudRain, ChevronDown, ChevronUp, AlertTriangle, BookOpen } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';

const MissionIntelWidget = ({ onLaunchBriefing }) => {
    const [intel, setIntel] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedItem, setExpandedItem] = useState(null);

    useEffect(() => {
        const fetchOracle = async () => {
            try {
                const data = await SYSTEM_API.getOracleFeed();
                setIntel(data);
            } catch (err) {
                console.error("Oracle offline", err);
            } finally {
                setLoading(false);
            }
        };
        fetchOracle();
    }, []);

    if (loading) return null; // Silent load
    if (!intel || intel.length === 0) return null; // Don't show if nothing relevant

    return (
        <div className="bg-white/[0.02] border border-purple-500/20 rounded-2xl overflow-hidden mb-6 relative group backdrop-blur-2xl shadow-[0_0_40px_rgba(0,0,0,0.2)]">
            {/* Glassmorphism Background */}
            <div className="absolute inset-0 bg-gradient-to-r from-purple-900/10 to-blue-900/10 backdrop-blur-sm pointer-events-none" />

            <div className="relative z-10 p-4">
                <div className="flex items-center gap-2 mb-4">
                    <Sparkles className="w-5 h-5 text-purple-400 animate-pulse" />
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest">Mission Intelligence</h3>
                    <div className="ml-auto px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-[10px] text-purple-300 font-mono">
                        ORACLE ACTIVE
                    </div>
                </div>

                <div className="space-y-3">
                    {intel.map((item, idx) => (
                        <div
                            key={idx}
                            className={`
                                rounded-xl border transition-all duration-300 overflow-hidden
                                ${item.trigger === 'Weather Alert'
                                    ? 'bg-red-500/10 border-red-500/30 hover:bg-red-500/20'
                                    : 'bg-slate-800/60 border-white/5 hover:bg-slate-800'
                                }
                            `}
                        >
                            <div
                                className="p-3 cursor-pointer flex items-start gap-3"
                                onClick={() => setExpandedItem(expandedItem === idx ? null : idx)}
                            >
                                <div className={`mt-0.5 p-1.5 rounded-lg ${item.trigger === 'Weather Alert' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                    {item.trigger === 'Weather Alert' ? <CloudRain className="w-4 h-4" /> : <BookOpen className="w-4 h-4" />}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <div className="flex justify-between items-start">
                                        <h4 className={`text-sm font-semibold truncate ${item.trigger === 'Weather Alert' ? 'text-red-100' : 'text-gray-200'}`}>
                                            {item.title}
                                        </h4>
                                        {expandedItem === idx ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
                                    </div>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className="text-[10px] font-mono text-gray-500 uppercase">{item.type}</span>
                                        <span className="text-[10px] font-mono text-gray-600">•</span>
                                        <span className="text-[10px] text-gray-400 truncate">Linked to: {item.phase_match}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Snippet Preview */}
                            {expandedItem === idx && (
                                <div className="px-3 pb-3 pt-0">
                                    <div className="bg-slate-950/50 rounded-lg p-3 text-xs text-gray-400 font-mono leading-relaxed border border-white/5">
                                        {item.snippet}
                                        <div className="mt-2 pt-2 border-t border-white/5 flex justify-between items-center">
                                            <button
                                                className="text-[10px] bg-purple-500/10 border border-purple-500/20 text-purple-400 px-2 py-1 rounded hover:bg-purple-500/20 uppercase font-bold tracking-wider"
                                                onClick={() => onLaunchBriefing && onLaunchBriefing({ phase_name: item.phase_match, project_name: "Active Project" })}
                                            >
                                                Launch Briefing
                                            </button>
                                            <button className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1 uppercase font-bold tracking-wider">
                                                <FileText className="w-3 h-3" />
                                                Open Full Document
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default MissionIntelWidget;
