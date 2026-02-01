import React from 'react';

const ActiveProjectsView = () => {
    return (
        <div className="p-10 text-center text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
            <h3 className="text-xl font-bold mb-2">🏗️ Active Projects</h3>
            <p className="mb-4">List of active projects for service calls and contract jobs.</p>
            <div className="flex gap-4 justify-center mt-4">
                <div className="p-4 bg-slate-700 rounded-lg">
                    <div className="text-2xl font-bold text-white">12</div>
                    <div className="text-xs text-slate-400 uppercase">Service Calls</div>
                </div>
                <div className="p-4 bg-slate-700 rounded-lg">
                    <div className="text-2xl font-bold text-white">5</div>
                    <div className="text-xs text-slate-400 uppercase">Contract Jobs</div>
                </div>
            </div>
        </div>
    );
};

export default ActiveProjectsView;
