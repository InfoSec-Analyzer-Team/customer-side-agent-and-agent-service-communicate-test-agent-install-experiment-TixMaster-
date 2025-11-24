import React from 'react';
import Link from 'next/link';
import { Event } from '@/utils/mockData';

interface EventCardProps {
    event: Event;
}

const EventCard: React.FC<EventCardProps> = ({ event }) => {
    return (
        <Link href={`/events/${event.id}`} className="block hover:opacity-90 transition-opacity">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-200 dark:border-gray-700">
                <div className="relative h-40 w-full">
                    <img
                        src={event.image}
                        alt={event.title}
                        className="w-full h-full object-cover"
                    />
                </div>
                <div className="p-4">
                    <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                        {event.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                        {new Date(event.date).toLocaleDateString('zh-TW')}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        {event.location}
                    </p>
                    <div className="flex justify-between items-center pt-2 border-t border-gray-100 dark:border-gray-700">
                        <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                            NT$ {event.price}
                        </span>
                        <span className="text-sm text-blue-600 dark:text-blue-400">
                            查看詳情 →
                        </span>
                    </div>
                </div>
            </div>
        </Link>
    );
};

export default EventCard;
