export interface Event {
    id: string;
    title: string;
    date: string;
    location: string;
    price: number;
    image: string;
    description: string;
}

export const MOCK_EVENTS: Event[] = [
    {
        id: '1',
        title: 'Neon Dreams Concert',
        date: '2025-12-15T19:00:00',
        location: 'Cyber Arena, Taipei',
        price: 2500,
        image: 'https://images.unsplash.com/photo-1459749411177-718bf998e889?auto=format&fit=crop&q=80&w=1000',
        description: 'Experience the future of music with Neon Dreams. A visual and auditory masterpiece.',
    },
    {
        id: '2',
        title: 'Tech Summit 2025',
        date: '2025-11-30T09:00:00',
        location: 'Grand Convention Center',
        price: 1200,
        image: 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&q=80&w=1000',
        description: 'Join the leading minds in technology for a day of innovation and networking.',
    },
    {
        id: '3',
        title: 'Classic Symphony Night',
        date: '2025-12-24T20:00:00',
        location: 'National Concert Hall',
        price: 3000,
        image: 'https://images.unsplash.com/photo-1465847899078-b413929f7120?auto=format&fit=crop&q=80&w=1000',
        description: 'A magical Christmas eve with the National Symphony Orchestra.',
    },
];
