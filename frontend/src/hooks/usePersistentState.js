import { useState, useEffect } from 'react';

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

    useEffect(() => {
        let isMounted = true;

        const revalidate = async () => {
            setIsRevalidating(true);
            try {
                const newData = await fetcherFn();

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
                    setState(newData);
                    try {
                        window.localStorage.setItem(key, JSON.stringify(newData));
                    } catch (e) {
                        console.error("LocalStorage Write Failed", e);
                    }
                }
            } catch (err) {
                console.warn(`Revalidation failed for "${key}", keeping stale data.`);
            } finally {
                if (isMounted) setIsRevalidating(false);
            }
        };

        revalidate();

        return () => { isMounted = false; };
    }, [key, fetcherFn]); // Ensure fetcherFn is stable (useCallback)

    return [state, isRevalidating];
};

export default usePersistentState;
