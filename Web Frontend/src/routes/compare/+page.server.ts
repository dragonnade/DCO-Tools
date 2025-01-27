// src/routes/compare/+page.server.ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
    console.log('Starting page load');
    try {
        // Return any data needed for initial page load
        console.log('Page load successful');
        return {
            // Initial state if needed
        };
    } catch (error) {
        console.error('Error during page load:', error);
        throw error;
    }
};