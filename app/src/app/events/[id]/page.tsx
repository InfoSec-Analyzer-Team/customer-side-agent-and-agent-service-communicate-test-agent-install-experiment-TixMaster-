import React from 'react';
import { MOCK_EVENTS } from '@/utils/mockData';
import ViewingCount from '@/components/ViewingCount';
import Link from 'next/link';
import { notFound } from 'next/navigation';

interface PageProps {
    params: Promise<{
        id: string;
    }>;
}

export default async function EventDetail({ params }: PageProps) {
    const resolvedParams = await params;
    const event = MOCK_EVENTS.find((e) => e.id === resolvedParams.id);

    if (!event) {
        return notFound();
    }

    return (
        <main className="min-h-screen p-6 md:p-8 max-w-4xl mx-auto">
            <Link href="/" className="text-blue-600 hover:underline mb-4 inline-block text-sm">
                ← 返回活動列表
            </Link>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="h-64 w-full">
                    <img
                        src={event.image}
                        alt={event.title}
                        className="w-full h-full object-cover"
                    />
                </div>

                <div className="p-6">
                    <h1 className="text-3xl font-bold mb-2">{event.title}</h1>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                        {new Date(event.date).toLocaleDateString('zh-TW')} • {event.location}
                    </p>

                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mb-6">
                        <h2 className="text-xl font-semibold mb-2">活動介紹</h2>
                        <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                            {event.description}
                        </p>
                    </div>

                    <ViewingCount />

                    <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg mt-6">
                        <div className="flex justify-between items-center mb-4">
                            <span className="text-gray-600 dark:text-gray-300">票價</span>
                            <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                                NT$ {event.price}
                            </span>
                        </div>

                        <Link
                            href={`/checkout?eventId=${event.id}`}
                            className="block w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white text-center font-semibold rounded-lg transition-colors"
                        >
                            立即購票
                        </Link>
                    </div>
                </div>
            </div>
        </main>
    );
}
