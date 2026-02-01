import React, { useState, useEffect, useCallback } from 'react';
import { SYSTEM_API } from '../../services/api';
import {
    MessageSquare,
    AlertTriangle,
    Lightbulb,
    CheckCircle,
    X,
    Send,
    Check,
    Clock,
    CornerUpLeft
} from 'lucide-react';

const DocumentCommentPanel = ({ documentPath, onClose }) => {
    const [comments, setComments] = useState([]);
    const [summary, setSummary] = useState(null);
    const [newComment, setNewComment] = useState('');
    const [commentType, setCommentType] = useState('general');
    const [author] = useState('Admin'); // TODO: Get from auth context
    const [isLoading, setIsLoading] = useState(false);

    const loadComments = useCallback(async () => {
        try {
            const data = await SYSTEM_API.getDocumentComments(documentPath);
            setComments(data);
        } catch (error) {
            console.error('Failed to load comments', error);
        }
    }, [documentPath]);

    const loadSummary = useCallback(async () => {
        try {
            const data = await SYSTEM_API.getReviewSummary(documentPath);
            setSummary(data);
        } catch (error) {
            console.error('Failed to load summary', error);
        }
    }, [documentPath]);

    useEffect(() => {
        loadComments();
        loadSummary();
    }, [loadComments, loadSummary]);

    const handleAddComment = async () => {
        if (!newComment.trim()) return;

        setIsLoading(true);
        try {
            await SYSTEM_API.addDocumentComment(documentPath, author, newComment, commentType);
            setNewComment('');
            setCommentType('general');
            await loadComments();
            await loadSummary();
        } catch (error) {
            alert('Failed to add comment: ' + error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleResolve = async (commentId) => {
        if (!confirm('Mark this comment as resolved?')) return;

        try {
            await SYSTEM_API.resolveComment(commentId, author);
            await loadComments();
            await loadSummary();
        } catch (error) {
            alert('Failed to resolve comment: ' + error.message);
        }
    };

    const handleDemote = async () => {
        if (!confirm('Return this document to Draft status?')) return;
        try {
            await SYSTEM_API.demoteToDraft(documentPath);
            onClose(); // Close panel on success
            // Ideally we should reload the main list but that's handled in the parent.
            // We can perhaps trigger a reload via a prop or just close.
            // For now, closing is fine, the user will see it's gone or can refresh.
            window.location.reload(); // Force refresh to update list state simply
        } catch (error) {
            alert('Failed to return to draft: ' + error.response?.data?.detail || error.message);
        }
    };

    const getTypeIcon = (type) => {
        switch (type) {
            case 'issue': return <AlertTriangle className="w-4 h-4 text-red-400" />;
            case 'suggestion': return <Lightbulb className="w-4 h-4 text-yellow-400" />;
            case 'approval': return <CheckCircle className="w-4 h-4 text-green-400" />;
            default: return <MessageSquare className="w-4 h-4 text-blue-400" />;
        }
    };

    const getTypeBadgeColor = (type) => {
        switch (type) {
            case 'issue': return 'bg-red-500/10 text-red-400 border-red-500/20';
            case 'suggestion': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
            case 'approval': return 'bg-green-500/10 text-green-400 border-green-500/20';
            default: return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-6">
            <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl">
                {/* Header */}
                <div className="p-6 border-b border-white/5 flex justify-between items-start">
                    <div>
                        <h2 className="text-xl font-bold text-white mb-1">Review Comments</h2>
                        <p className="text-sm text-gray-400 font-mono">{documentPath.split('\\').pop()}</p>
                        {summary && (
                            <div className="flex gap-3 mt-3 text-xs">
                                <span className="text-gray-400">Total: {summary.total_comments}</span>
                                <span className="text-amber-400">Unresolved: {summary.unresolved_total}</span>
                                <span className="text-red-400">Issues: {summary.unresolved_issues}</span>
                                {summary.can_sign_off && (
                                    <span className="text-green-400 flex items-center gap-1">
                                        <Check className="w-3 h-3" /> Ready for Sign-Off
                                    </span>
                                )}
                            </div>
                        )}
                    </div>
                    <div className="flex gap-2 items-start">
                        {documentPath.includes('.REVIEW-v') && (
                            <button
                                onClick={handleDemote}
                                className="text-xs px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-lg font-bold transition-all flex items-center gap-2"
                            >
                                <CornerUpLeft className="w-3.5 h-3.5" /> Return to Draft
                            </button>
                        )}
                        <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                            <X className="w-6 h-6" />
                        </button>
                    </div>
                </div>

                {/* Comments List */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {comments.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-20" />
                            <p>No comments yet. Be the first to add feedback!</p>
                        </div>
                    ) : (
                        comments.map((comment) => (
                            <div
                                key={comment.comment_id}
                                className={`bg-slate-950/50 border rounded-lg p-4 ${comment.is_resolved
                                    ? 'border-white/5 opacity-60'
                                    : 'border-white/10'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-3">
                                    <div className="flex items-center gap-2">
                                        {getTypeIcon(comment.comment_type)}
                                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${getTypeBadgeColor(comment.comment_type)}`}>
                                            {comment.comment_type}
                                        </span>
                                        <span className="text-sm font-semibold text-white">{comment.author}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-gray-500 font-mono flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {new Date(comment.created_at).toLocaleDateString()}
                                        </span>
                                        {!comment.is_resolved && (
                                            <button
                                                onClick={() => handleResolve(comment.comment_id)}
                                                className="text-xs px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold transition-all"
                                            >
                                                Resolve
                                            </button>
                                        )}
                                    </div>
                                </div>
                                <p className="text-sm text-gray-300 leading-relaxed">{comment.content}</p>
                                {comment.is_resolved && (
                                    <div className="mt-3 pt-3 border-t border-white/5 text-xs text-green-400 flex items-center gap-1">
                                        <Check className="w-3 h-3" />
                                        Resolved by {comment.resolved_by} on {new Date(comment.resolved_at).toLocaleDateString()}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>

                {/* Add Comment Form */}
                <div className="p-6 border-t border-white/5 bg-slate-950/30">
                    <div className="flex gap-3 mb-3">
                        {['general', 'issue', 'suggestion', 'approval'].map((type) => (
                            <button
                                key={type}
                                onClick={() => setCommentType(type)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${commentType === type
                                    ? 'bg-purple-600 text-white shadow-lg'
                                    : 'bg-slate-800 text-gray-400 hover:bg-slate-700'
                                    }`}
                            >
                                {getTypeIcon(type)}
                                {type.charAt(0).toUpperCase() + type.slice(1)}
                            </button>
                        ))}
                    </div>
                    <div className="flex gap-3">
                        <textarea
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            placeholder={`Add a ${commentType}...`}
                            className="flex-1 bg-slate-800 border border-white/10 rounded-lg px-4 py-3 text-sm text-white resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                            rows={3}
                        />
                        <button
                            onClick={handleAddComment}
                            disabled={isLoading || !newComment.trim()}
                            className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg font-bold transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/20"
                        >
                            <Send className="w-4 h-4" />
                            Post
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DocumentCommentPanel;
