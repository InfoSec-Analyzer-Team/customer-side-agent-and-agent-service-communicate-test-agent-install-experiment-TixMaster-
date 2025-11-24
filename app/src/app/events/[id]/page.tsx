import React from 'react';
import { MOCK_EVENTS } from '@/utils/mockData';
import ViewingCount from '@/components/ViewingCount';
import Link from 'next/link';
import { notFound } from 'next/navigation';

interface PageProps {
    params: {
        id: string;
    };
    <main className = "min-h-screen p-8 max-w-5xl mx-auto">
            <Link href = "/" className = "text-blue-600 hover:underline mb-4 inline-block">
                & larr; Back to Events
            </Link >

    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
        <div className="relative h-96 w-full">
            <img
                src={event.image}
                alt={event.title}
                className="w-full h-full object-cover"
            />
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-8">
                <h1 className="text-4xl font-bold text-white mb-2">{event.title}</h1>
                <p className="text-xl text-gray-200">
                    {new Date(event.date).toLocaleDateString()} • {event.location}
                </p>
            </div>
        </div>

        <div className="p-8 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="md:col-span-2 space-y-6">
                <section>
                    <h2 className="text-2xl font-bold mb-4">About this Event</h2>
                    <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                        {event.description}
                    </p>
                </section>

                <ViewingCount />
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 p-6 rounded-xl h-fit sticky top-8">
                <h3 className="text-xl font-bold mb-4">Get Tickets</h3>
                <div className="flex justify-between items-center mb-6">
                    <span className="text-gray-600 dark:text-gray-300">General Admission</span>
                    <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                        ${event.price}
                    </span>
                </div>

                <Link
                    href={`/checkout?eventId=${event.id}`}
                    className="block w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white text-center font-bold rounded-lg transition-colors shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                >
                    Buy Now
                </Link>
                <p className="text-xs text-center text-gray-500 mt-4">
                    Secure payment powered by TixMaster
                </p>
            </div>
        </div>
    </div>
        </main >
    );
}
