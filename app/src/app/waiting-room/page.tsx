import React from 'react';

export default function WaitingRoom() {
    return (
        <main className="min-h-screen flex flex-col items-center justify-center bg-blue-600 text-white p-4 text-center">
            <div className="mb-8 animate-bounce">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-24 w-24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <h1 className="text-4xl font-bold mb-4">You are in the Waiting Room</h1>
            <p className="text-xl max-w-md mb-8">
                Due to high demand, we have placed you in a queue. Please do not refresh this page. You will be redirected automatically when it's your turn.
            </p>
            <div className="w-64 h-2 bg-blue-800 rounded-full overflow-hidden">
                <div className="h-full bg-white animate-progress origin-left w-full"></div>
            </div>
            <p className="mt-4 text-sm opacity-75">Estimated wait time: 2 minutes</p>
        </main>
    );
}
