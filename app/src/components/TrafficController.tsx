'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export default function TrafficController() {
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        // Skip check if already in waiting room
        if (pathname === '/waiting-room') return;

        // Check if high traffic simulation is enabled
        const isHighTraffic = localStorage.getItem('FORCE_HIGH_TRAFFIC') === 'true';

        if (isHighTraffic) {
            // 30% chance to be redirected to waiting room on page load if high traffic is "on"
            // Or just force it for testing purposes
            const shouldRedirect = Math.random() > 0.3;

            if (shouldRedirect) {
                console.log('High traffic detected! Redirecting to waiting room...');
                router.push('/waiting-room');
            }
        }
    }, [pathname, router]);

    return null;
}
