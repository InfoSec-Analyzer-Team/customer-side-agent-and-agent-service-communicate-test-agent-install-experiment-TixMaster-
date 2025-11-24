'use client';

import React, { useState, useEffect } from 'react';
import { FEATURE_FLAGS } from '@/config/flags';
import { useRouter } from 'next/navigation';

const CountdownTimer: React.FC = () => {
    const [timeLeft, setTimeLeft] = useState<number>(600); // 10 minutes in seconds
    const router = useRouter();

    useEffect(() => {
        if (!FEATURE_FLAGS.ENABLE_CHECKOUT_TIMER) return;

        const timer = setInterval(() => {
            setTimeLeft((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    alert('Time expired! Redirecting to home...');
                    router.push('/');
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [router]);

    if (!FEATURE_FLAGS.ENABLE_CHECKOUT_TIMER) return null;

    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;

    return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center justify-between">
            <div className="flex items-center text-red-700">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-semibold">Tickets are held for:</span>
            </div>
            <div className="text-2xl font-mono font-bold text-red-600">
                {minutes.toString().padStart(2, '0')}:{seconds.toString().padStart(2, '0')}
            </div>
        </div>
    );
};

export default CountdownTimer;
