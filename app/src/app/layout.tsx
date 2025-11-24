import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import TrafficController from '@/components/TrafficController';
import DevTools from '@/components/DevTools';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'TixMaster',
    description: 'Secure Ticket Sales System',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <TrafficController />
                {children}
                <DevTools />
            </body>
        </html>
    );
}
