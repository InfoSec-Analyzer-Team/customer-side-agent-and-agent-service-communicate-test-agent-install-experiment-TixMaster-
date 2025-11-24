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
                <h2 className="text-2xl font-bold mb-4">Event not found</h2>
                <Link href="/" className="text-blue-600 hover:underline">Return Home</Link>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto">
            <h1 className="text-3xl font-bold mb-8">Checkout</h1>

            <CountdownTimer />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                        <h2 className="text-xl font-bold mb-4">Order Summary</h2>
                        <div className="flex items-start space-x-4 mb-4">
                            <img src={event.image} alt={event.title} className="w-20 h-20 object-cover rounded" />
                            <div>
                                <h3 className="font-bold">{event.title}</h3>
                                <p className="text-sm text-gray-500">{new Date(event.date).toLocaleDateString()}</p>
                                <p className="text-sm text-gray-500">{event.location}</p>
                            </div>
                        </div>
                        <div className="border-t pt-4 flex justify-between items-center font-bold text-lg">
                            <span>Total</span>
                            <span>${event.price}</span>
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                    <h2 className="text-xl font-bold mb-4">Payment Details</h2>
                    <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
                        <div>
                            <label className="block text-sm font-medium mb-1">Card Number</label>
                            <input type="text" placeholder="0000 0000 0000 0000" className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Expiry</label>
                                <input type="text" placeholder="MM/YY" className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">CVC</label>
                                <input type="text" placeholder="123" className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600" />
                            </div>
                        </div>
                        <button className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-lg mt-4 transition-colors">
                            Complete Payment
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}

export default function Checkout() {
    return (
        <main className="min-h-screen p-8 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white">
            <Suspense fallback={<div>Loading...</div>}>
                <CheckoutContent />
            </Suspense>
        </main>
    );
}
