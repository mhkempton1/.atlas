import React, { useState } from 'react';
import { Save, X, Eye, Edit3 } from 'lucide-react';

const DocumentEditor = ({ doc, onSave, onCancel }) => {
    const [content, setContent] = useState(doc?.content || '');
    const [preview, setPreview] = useState(false);

    const handleSave = () => {
        onSave(content);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <div className="w-full max-w-5xl h-[90vh] glass-panel p-0 flex flex-col overflow-hidden border-yellow-400/30">
                {/* Header */}
                <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/5">
                    <div className="flex items-center gap-3">
                        <Edit3 className="w-5 h-5 text-yellow-400" />
                        <div>
                            <h3 className="font-bold text-white leading-none mb-1">Editing: {doc?.filename || 'New Document'}</h3>
                            <p className="text-xs text-text-muted">Direct OneDrive Edit (LOCKED-STRICT)</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPreview(!preview)}
                            className={`btn ${preview ? 'btn-primary' : 'btn-secondary'} text-xs flex items-center gap-2`}
                        >
                            {preview ? <Edit3 className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                            {preview ? 'Edit' : 'Preview'}
                        </button>
                        <div className="h-6 w-px bg-white/10 mx-2" />
                        <button onClick={onCancel} className="btn btn-secondary text-xs flex items-center gap-2">
                            <X className="w-3 h-3" /> Cancel
                        </button>
                        <button onClick={handleSave} className="btn btn-primary text-xs flex items-center gap-2">
                            <Save className="w-3 h-3" /> Save Changes
                        </button>
                    </div>
                </div>

                {/* Editor Content */}
                <div className="flex-1 flex overflow-hidden">
                    {!preview ? (
                        <textarea
                            className="w-full h-full bg-slate-950 p-6 text-slate-300 font-mono text-sm resize-none focus:outline-none focus:ring-1 focus:ring-yellow-400/50"
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            placeholder="Start writing your company guideline or SOP here..."
                            spellCheck="false"
                        />
                    ) : (
                        <div className="w-full h-full bg-slate-900 p-8 overflow-y-auto prose prose-invert max-w-none">
                            {/* Simple line break parsing for preview since we don't have a MD library yet */}
                            {content.split('\n').map((line, i) => (
                                <p key={i} className="mb-2">{line || <br />}</p>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-2 border-t border-white/10 bg-black/40 text-[10px] text-text-muted flex justify-between px-4 italic">
                    <span>Draft Status: LOCAL_EDIT_SESSION</span>
                    <span>MD_SYNTAX_ENABLED</span>
                </div>
            </div>
        </div>
    );
};

export default DocumentEditor;
