'use client';

import React, { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { MOCK_EVENTS } from '@/utils/mockData';
import CountdownTimer from '@/components/CountdownTimer';
import Link from 'next/link';

function CheckoutContent() {
    const searchParams = useSearchParams();
    const eventId = searchParams.get('eventId');
    const event = MOCK_EVENTS.find((e) => e.id === eventId);

    if (!event) {
        return (
            <div className="text-center py-20">
                <h2 className="text-2xl font-bold mb-4">找不到活動</h2>
                <Link href="/" className="text-blue-600 hover:underline">返回首頁</Link>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">結帳</h1>

            <CountdownTimer />

            <div className="space-y-6">
                <div className="bg-white dark:bg-gray-800 p-5 rounded-lg shadow border border-gray-200 dark:border-gray-700">
                    <h2 className="text-lg font-semibold mb-4">訂單摘要</h2>
                    <div className="flex items-start space-x-4 mb-4">
                        <img src={event.image} alt={event.title} className="w-16 h-16 object-cover rounded" />
                        <div className="flex-1">
                            <h3 className="font-semibold text-sm">{event.title}</h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{new Date(event.date).toLocaleDateString('zh-TW')}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{event.location}</p>
                        </div>
                    </div>
                    <div className="border-t border-gray-200 dark:border-gray-700 pt-3 flex justify-between items-center font-semibold">
                        <span>總計</span>
                        <span className="text-lg">NT$ {event.price}</span>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 p-5 rounded-lg shadow border border-gray-200 dark:border-gray-700">
                    <h2 className="text-lg font-semibold mb-4">付款資訊</h2>
                    <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
                        <div>
                            <label className="block text-sm font-medium mb-1">信用卡號</label>
                            <input type="text" placeholder="0000 0000 0000 0000" className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 text-sm" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">有效期限</label>
                                <input type="text" placeholder="MM/YY" className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 text-sm" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">安全碼</label>
                                <input type="text" placeholder="123" className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 text-sm" />
                            </div>
                        </div>
                        <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg mt-4 transition-colors">
                            確認付款
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}

export default function Checkout() {
    return (
        <main className="min-h-screen p-6 md:p-8 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white">
            <Suspense fallback={<div>載入中...</div>}>
                <CheckoutContent />
            </Suspense>
        </main>
    );
}
