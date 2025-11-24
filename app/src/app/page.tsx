import React from 'react';
import { MOCK_EVENTS } from '@/utils/mockData';
import EventCard from '@/components/EventCard';

export default function Home() {
    return (
        <main className="min-h-screen p-8 max-w-7xl mx-auto">
            <header className="mb-12 text-center">
                <h1 className="text-5xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
                    TixMaster
                </h1>
                <p className="text-xl text-gray-600 dark:text-gray-300">
                    Your gateway to unforgettable experiences.
                </p>
            </header>

            <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {MOCK_EVENTS.map((event) => (
                    <EventCard key={event.id} event={event} />
                ))}
            </section>
        </main>
    );
}
