import axios from 'axios';

const API_URL = 'http://127.0.0.1:4201/api/v1';
const ALTIMETER_API_URL = 'http://127.0.0.1:4203/api/v1';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const SYSTEM_API = {
    checkHealth: async () => {
        try {
            const response = await api.get('/health');
            return response.data;
        } catch (error) {
            console.error("API Health Check Failed", error);
            return { status: 'offline' };
        }
    },

    generateDraft: async (sender, subject, body, instructions) => {
        const response = await api.post('/agents/draft', {
            sender,
            subject,
            body,
            instructions
        });
        return response.data;
    },

    sendEmail: async (recipient, subject, body) => {
        const response = await api.post('/agents/send-email', {
            recipient,
            subject,
            body
        });
        return response.data;
    },

    getKnowledgeDocs: async () => {
        const response = await api.get('/knowledge/docs');
        return response.data;
    },

    getKnowledgeContent: async (path) => {
        const response = await api.get(`/knowledge/content?path=${encodeURIComponent(path)}`);
        return response.data.content;
    },

    searchKnowledge: async (query) => {
        const response = await api.get(`/knowledge/search?q=${encodeURIComponent(query)}`);
        return response.data;
    },

    reindexKnowledgeBase: async () => {
        const response = await api.post('/knowledge/reindex');
        return response.data;
    },

    // Document Control
    getControlledDocs: async () => {
        const response = await api.get('/docs/list');
        return response.data;
    },

    getDashboardStats: async () => {
        const response = await api.get('/dashboard/stats');
        return response.data;
    },

    getActivityLog: async () => {
        const response = await api.get('/system/activity');
        return response.data;
    },

    getDocContent: async (path) => {
        const response = await api.get(`/docs/content?path=${encodeURIComponent(path)}`);
        return response.data.content;
    },

    createDraft: async (title, content, section = "GUIDELINES") => {
        const response = await api.post('/docs/draft/create', { title, content, section });
        return response.data;
    },

    saveDraft: async (path, content) => {
        const response = await api.post('/docs/draft/save', { path, content });
        return response.data;
    },

    deleteDraft: async (path) => {
        const response = await api.delete(`/docs/draft?path=${encodeURIComponent(path)}`);
        return response.data;
    },

    promoteToReview: async (path) => {
        const response = await api.post('/docs/promote', { path });
        return response.data;
    },

    demoteToDraft: async (path) => {
        const response = await api.post('/docs/demote', { path });
        return response.data;
    },

    lockDocument: async (path, approver) => {
        const response = await api.post('/docs/lock', { path, approver });
        return response.data;
    },

    importToReview: async (path, section = 'GUIDELINES') => {
        const response = await api.post('/docs/import', { path, section });
        return response.data;
    },

    // Document Comments
    addDocumentComment: async (path, author, content, commentType = 'general') => {
        const response = await api.post('/docs/comment', {
            path,
            author,
            content,
            comment_type: commentType
        });
        return response.data;
    },

    getDocumentComments: async (path) => {
        const response = await api.get(`/docs/comments?path=${encodeURIComponent(path)}`);
        return response.data;
    },

    resolveComment: async (commentId, resolver) => {
        const response = await api.patch(`/docs/comment/${commentId}/resolve`, { resolver });
        return response.data;
    },

    getReviewSummary: async (path) => {
        const response = await api.get(`/docs/review-summary?path=${encodeURIComponent(path)}`);
        return response.data;
    },

    // System Control
    triggerAction: async (action) => {
        const response = await api.post(`/system/control/${action}`);
        return response.data;
    },

    getAltimeterProjects: async () => {
        const response = await api.get('/system/altimeter/projects');
        return response.data;
    },

    // Email Actions
    replyToEmail: async (emailId, body, replyAll = false) => {
        const response = await api.post(`/email/${emailId}/reply`, { body, reply_all: replyAll });
        return response.data;
    },

    forwardEmail: async (emailId, toAddress, note = '') => {
        const response = await api.post(`/email/${emailId}/forward`, { to_address: toAddress, note });
        return response.data;
    },

    deleteEmail: async (emailId) => {
        const response = await api.delete(`/email/${emailId}`);
        return response.data;
    },

    archiveEmail: async (emailId) => {
        const response = await api.post(`/email/${emailId}/archive`);
        return response.data;
    },

    markUnread: async (emailId) => {
        const response = await api.post(`/email/${emailId}/unread`);
        return response.data;
    },

    moveEmail: async (emailId, labelName) => {
        const response = await api.post(`/email/${emailId}/move`, { label_name: labelName });
        return response.data;
    },

    // Intelligent Email Features
    scanEmails: async (limit = 10) => {
        const response = await api.post(`/email/scan?limit=${limit}`);
        return response.data;
    },

    extractTasks: async (emailId) => {
        const response = await api.post(`/tasks/extract/${emailId}`);
        return response.data;
    },

    extractTasksFromEmail: async (emailId) => {
        const response = await api.post(`/tasks/extract/${emailId}`);
        return response.data;
    },

    generateReplyDraft: async (emailId, instructions) => {
        const response = await api.post(`/email/${emailId}/draft-reply`, { instructions });
        return response.data;
    },

    updateEmailCategory: async (emailId, category) => {
        const response = await api.put(`/email/${emailId}/category`, { category });
        return response.data;
    },

    getLabels: async () => {
        const response = await api.get('/email/labels');
        return response.data;
    },

    // Calendar
    getCalendarEvents: async (days = 14) => {
        const response = await api.get(`/calendar/events?days=${days}`);
        return response.data;
    },

    getTodayEvents: async () => {
        const response = await api.get('/calendar/today');
        return response.data;
    },

    getUnifiedSchedule: async () => {
        const response = await api.get('/dashboard/schedule');
        return response.data;
    },

    syncCalendar: async () => {
        const response = await api.post('/calendar/sync');
        return response.data;
    },

    // Task CRUD
    getTasks: async (filters = {}) => {
        const params = new URLSearchParams();
        if (filters.status) params.append('status', filters.status);
        if (filters.priority) params.append('priority', filters.priority);
        if (filters.category) params.append('category', filters.category);
        const response = await api.get(`/tasks/list?${params.toString()}`);
        return response.data;
    },

    createTask: async (task) => {
        const response = await api.post('/tasks/create', task);
        return response.data;
    },

    updateTask: async (taskId, updates) => {
        const response = await api.put(`/tasks/${taskId}`, updates);
        return response.data;
    },

    deleteTask: async (taskId) => {
        const response = await api.delete(`/tasks/${taskId}`);
        return response.data;
    },

    getWeather: async (lat = null, lon = null) => {
        const params = new URLSearchParams();
        if (lat !== null && lon !== null) {
            params.append('lat', lat);
            params.append('lon', lon);
        }
        const response = await api.get(`/weather/forecast?${params.toString()}`);
        return response.data;
    },

    sendMessage: async (message) => {
        const response = await api.post('/chat', { message });
        return response.data;
    },

    getOracleFeed: async () => {
        const response = await api.get('/dashboard/oracle');
        return response.data;
    },

    // Foreman Protocol
    generateMissionBriefing: async (phaseId, sopContent) => {
        const response = await api.post('/foreman/briefing', { phase_id: phaseId, sop_content: sopContent });
        return response.data;
    },

    draftDailyLog: async (data) => {
        const response = await api.post('/reporting/daily-log/draft', data);
        return response.data;
    },

    updateTaskStatus: async (taskId, status, safetyAck = false) => {
        const response = await api.put(`/tasks/${taskId}`, { status, safety_ack: safetyAck });
        return response.data;
    }
};

export default api;
