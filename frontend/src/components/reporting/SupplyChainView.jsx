import React from 'react';

const SupplyChainView = () => {
    return (
        <div className="p-10 text-center text-slate-500 border-2 border-dashed border-white/5 rounded-xl">
            <h3 className="text-xl font-bold mb-2">🚚 Supply Chain & Production</h3>
            <p className="mb-4">Tracking from delivery to received, and production line status.</p>
            <div className="mt-6 w-full max-w-lg mx-auto bg-white/5 rounded-full h-4 overflow-hidden">
                <div className="bg-indigo-500 h-full w-2/3 animate-pulse"></div>
            </div>
            <p className="text-xs text-indigo-400 mt-2">Production Line Active</p>
        </div>
    );
};

export default SupplyChainView;
