import { useState, useEffect, useRef } from 'react';

const usePersistentState = (key, fetcherFn, initialValue = null) => {
    // 1. Initialize from localStorage if available
    const [state, setState] = useState(() => {
        try {
            const item = window.localStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            console.error(`Error reading localStorage key "${key}":`, error);
            return initialValue;
        }
    });

    const [isRevalidating, setIsRevalidating] = useState(false);

    // Store the fetcherFn in a ref to keep it stable across renders
    const fetcherRef = useRef(fetcherFn);
    useEffect(() => {
        fetcherRef.current = fetcherFn;
    }, [fetcherFn]);

    useEffect(() => {
        let isMounted = true;

        const revalidate = async () => {
            setIsRevalidating(true);
            try {
                // Use the latest fetcherFn from the ref
                const newData = await fetcherRef.current();

                if (isMounted) {
                    setState(newData);
                    try {
                        window.localStorage.setItem(key, JSON.stringify(newData));
                    } catch (e) {
                        console.error("LocalStorage Write Failed", e);
                    }
                }
            } catch (err) {
                // Silent Fallback: If timeout (isSilentTimeout) or other error, do nothing.
                // Keep the stale state.
                console.warn(`Revalidation failed for "${key}", keeping stale data.`, err);
            } finally {
                if (isMounted) setIsRevalidating(false);
            }
        };

        revalidate();

        return () => { isMounted = false; };
    }, [key]); // Only depend on the key, not the unstable fetcherFn

    return [state, isRevalidating];
};

export default usePersistentState;
