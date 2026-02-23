import DOMPurify from './dompurify.js';

export const sanitize = (content) => {
    // Attempt to get the purifier instance either from import or window
    const purifier = DOMPurify || (typeof window !== 'undefined' ? window.DOMPurify : null);

    if (purifier && typeof purifier.sanitize === 'function') {
        return purifier.sanitize(content);
    }

    console.warn("DOMPurify not available, returning empty string for safety.");
    return "";
};
