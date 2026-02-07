import React from 'react';
import { Target, FileText, Calendar, Info } from 'lucide-react';

/**
 * MissionIntelSnippet - A premium glassmorphic display for Altimeter-bridged intel.
 */
const MissionIntelSnippet = ({ intel, type = 'sop' }) => {
    if (!intel) return null;

    const getIcon = () => {
        switch (type) {
            case 'sop': return <FileText className="w-3.5 h-3.5 text-emerald-400" />;
            case 'milestone': return <Calendar className="w-3.5 h-3.5 text-purple-400" />;
            case 'project': return <Target className="w-3.5 h-3.5 text-blue-400" />;
            default: return <Info className="w-3.5 h-3.5 text-gray-400" />;
        }
    };

    return (
        <div className="mission-intel-snippet my-2 group">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.03] border border-white/5 hover:border-emerald-500/20 transition-all backdrop-blur-md">
                <div className="mt-0.5 p-1.5 rounded-md bg-white/5 border border-white/10 group-hover:border-emerald-500/30 transition-colors">
                    {getIcon()}
                </div>
                <div className="flex-1 min-w-0">
                    <div className="text-[10px] font-bold text-emerald-500/70 uppercase tracking-tighter mb-0.5">
                        Mission Intel // {type}
                    </div>
                    <div className="text-sm font-medium text-gray-200 mb-1 leading-tight">
                        {intel.title || intel.phase_name}
                    </div>
                    {intel.snippet && (
                        <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
                            {intel.snippet}
                        </p>
                    )}
                    {intel.date_text && (
                        <div className="mt-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-purple-500/10 border border-purple-500/20 text-[9px] font-mono text-purple-400">
                            <Calendar className="w-2.5 h-2.5" />
                            DETECTION: {intel.date_text}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MissionIntelSnippet;
