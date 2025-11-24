'use client';

import React, { useState, useEffect } from 'react';
import { FEATURE_FLAGS } from '@/config/flags';

const ViewingCount: React.FC = () => {
    const [count, setCount] = useState<number>(0);

    useEffect(() => {
        if (FEATURE_FLAGS.ENABLE_VIEWING_COUNT) {
            // Randomize count between 50 and 200
            setCount(Math.floor(Math.random() * 150) + 50);
        }
    }, []);

    if (!FEATURE_FLAGS.ENABLE_VIEWING_COUNT) return null;

    return (
        <div className="flex items-center space-x-2 text-red-600 font-semibold animate-pulse">
            <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
            >
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                <path
                    fillRule="evenodd"
                    d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                    clipRule="evenodd"
                />
            </svg>
            <span>{count} people are viewing this event right now!</span>
        </div>
    );
};

export default ViewingCount;
