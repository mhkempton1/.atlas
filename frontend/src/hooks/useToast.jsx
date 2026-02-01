import { useState, useCallback, useMemo } from 'react';
import React from 'react';
import { Toast } from '../components/shared/UIComponents';

export const useToast = () => {
    const [toastData, setToastData] = useState(null);

    const toast = useCallback((message, type = 'info') => {
        setToastData({ message, type });
    }, []);

    const toastElement = useMemo(() => toastData ? (
        <Toast {...toastData} onClose={() => setToastData(null)} />
    ) : null, [toastData]);

    return {
        toast,
        toastElement,
        addToast: toast,
        ToastContainer: () => toastElement
    };
};
