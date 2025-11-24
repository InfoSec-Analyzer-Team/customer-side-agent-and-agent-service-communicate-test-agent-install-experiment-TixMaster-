'use client';

import React, { useState, useEffect } from 'react';

export default function DevTools() {
    const [isHighTraffic, setIsHighTraffic] = useState(false);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        setIsHighTraffic(localStorage.getItem('FORCE_HIGH_TRAFFIC') === 'true');
    }, []);

    const toggleTraffic = () => {
        const newState = !isHighTraffic;
        setIsHighTraffic(newState);
        localStorage.setItem('FORCE_HIGH_TRAFFIC', String(newState));
        if (newState) {
            alert('High Traffic Mode ENABLED. You may be redirected to Waiting Room on navigation.');
        } else {
            alert('High Traffic Mode DISABLED.');
        }
    };

    if (!isVisible) {
        return (
            <button
                onClick={() => setIsVisible(true)}
                className="fixed bottom-4 right-4 bg-gray-800 text-white p-2 rounded-full shadow-lg z-50 opacity-50 hover:opacity-100"
            >
                🛠️
            </button>
        );
    }

    return (
        <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 p-4 rounded-lg shadow-xl z-50 border border-gray-200 dark:border-gray-700 w-64">
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold">Dev Tools</h3>
                <button onClick={() => setIsVisible(false)} className="text-gray-500">✕</button>
            </div>

            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <span className="text-sm">Simulate High Traffic</span>
                    <button
                        onClick={toggleTraffic}
                        className={`w-12 h-6 rounded-full p-1 transition-colors ${isHighTraffic ? 'bg-green-500' : 'bg-gray-300'}`}
                    >
                        <div className={`w-4 h-4 bg-white rounded-full shadow-md transform transition-transform ${isHighTraffic ? 'translate-x-6' : ''}`} />
                    </button>
                </div>
                <p className="text-xs text-gray-500">
                    When enabled, navigation has a chance to redirect to Waiting Room.
                </p>
            </div>
        </div>
    );
}
