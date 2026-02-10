import React, { useState, useCallback } from 'react';
import EmailList from './EmailList';
import EmailView from './EmailView';

const EmailModule = () => {
    const [selectedEmail, setSelectedEmail] = useState(null);
    const [viewMode, setViewMode] = useState('list');
    const [refreshKey, setRefreshKey] = useState(0);

    const handleSelectEmail = (email) => {
        setSelectedEmail(email);
        setViewMode('view');
    };

    const handleEmailAction = useCallback((action, id, data) => {
        // After delete/archive, deselect and refresh list
        if (action === 'deleted' || action === 'archived') {
            setSelectedEmail(null);
            setViewMode('list');
            setRefreshKey(prev => prev + 1); // Force EmailList to re-fetch
        }
        if (action === 'unread' || action === 'update') {
            if (data) {
                setSelectedEmail(prev => prev && prev.email_id === id ? { ...prev, ...data } : prev);
            }
            setRefreshKey(prev => prev + 1);
        }
    }, [setSelectedEmail, setViewMode, setRefreshKey]);

    return (
        <div className="email-module h-[calc(100vh-100px)] flex gap-4">
            <div className={`${viewMode === 'view' ? 'hidden md:block' : 'block'} w-full md:w-1/3 h-full`}>
                <EmailList key={refreshKey} onSelectEmail={handleSelectEmail} />
            </div>

            <div className={`${viewMode === 'list' ? 'hidden md:block' : 'block'} w-full md:w-2/3 h-full`}>
                {selectedEmail ? (
                    <EmailView
                        email={selectedEmail}
                        onBack={() => setViewMode('list')}
                        onEmailAction={handleEmailAction}
                    />
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-text-muted bg-white/[0.01] rounded-lg border border-white/5 backdrop-blur-sm">
                        <div className="mb-4 text-6xl opacity-20">✉️</div>
                        <p>Select an email to view details</p>
                        <p className="text-sm opacity-50">or sync to fetch new messages</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default EmailModule;
