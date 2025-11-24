'use client';

import React, { useState, useEffect } from 'react';
import { FEATURE_FLAGS } from '@/config/flags';
import { useRouter } from 'next/navigation';

const CountdownTimer: React.FC = () => {
    const [timeLeft, setTimeLeft] = useState<number>(600);
    const router = useRouter();

    useEffect(() => {
        if (!FEATURE_FLAGS.ENABLE_CHECKOUT_TIMER) return;

        const timer = setInterval(() => {
            setTimeLeft((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    alert('時間到！返回首頁...');
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
        <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-3 mb-6 flex items-center justify-between">
            <div className="flex items-center text-orange-700 dark:text-orange-400 text-sm">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>保留時間：</span>
            </div>
            <div className="text-xl font-mono font-semibold text-orange-700 dark:text-orange-400">
                {minutes.toString().padStart(2, '0')}:{seconds.toString().padStart(2, '0')}
            </div>
        </div>
    );
};

export default CountdownTimer;
