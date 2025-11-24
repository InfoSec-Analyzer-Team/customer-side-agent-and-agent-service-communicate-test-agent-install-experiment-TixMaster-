import React from 'react';
import Link from 'next/link';
import { Event } from '@/utils/mockData';

interface EventCardProps {
    event: Event;
}

const EventCard: React.FC<EventCardProps> = ({ event }) => {
    return (
        <Link href={`/events/${event.id}`} className="group block">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden transition-transform transform group-hover:scale-105 duration-300">
                <div className="relative h-48 w-full">
                    <img
                        src={event.image}
                        alt={event.title}
                        className="w-full h-full object-cover"
                    />
                </div>
                <div className="p-4">
                    <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
                        {event.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
                        📅 {new Date(event.date).toLocaleDateString()}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                        📍 {event.location}
                    </p>
                    <div className="flex justify-between items-center">
                        <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                            ${event.price}
                        </span>
                        <span className="px-3 py-1 bg-blue-600 text-white text-sm rounded-full group-hover:bg-blue-700 transition-colors">
                            Buy Tickets
                        </span>
                    </div>
                </div>
            </div>
        </Link>
    );
};

export default EventCard;
