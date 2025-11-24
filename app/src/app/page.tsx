import React from 'react';
import { MOCK_EVENTS } from '@/utils/mockData';
import EventCard from '@/components/EventCard';

export default function Home() {
    return (
        <main className="min-h-screen p-6 md:p-8 max-w-6xl mx-auto">
            <header className="mb-8">
                <h1 className="text-4xl font-bold mb-2">TixMaster</h1>
                <p className="text-gray-600 dark:text-gray-400">選擇您想參加的活動</p>
            </header>

            <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {MOCK_EVENTS.map((event) => (
                    <EventCard key={event.id} event={event} />
                ))}
            </section>
        </main>
    );
}
