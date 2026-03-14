import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    // In a real app, this comes from the backend/auth context
    const [currentUser, setCurrentUser] = useState({
        name: "Michael Kempton",
        role: "Administrator",
        strata: 5 // 4+ = Admin/System Access
    });

    return (
        <AuthContext.Provider value={{ currentUser, setCurrentUser }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
