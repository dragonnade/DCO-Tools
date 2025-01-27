// /src/routes/api/legislation/+server.ts
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const log = {
    info: (...args: any[]) => {
        console.log('[Legislation API]', ...args);
    },
    error: (...args: any[]) => {
        console.error('[Legislation API ERROR]', ...args);
    }
};

export const GET: RequestHandler = async ({ url, request }) => {
    log.info('Incoming request:', {
        url: url.toString(),
        params: Object.fromEntries(url.searchParams),
        headers: Object.fromEntries(request.headers)
    });

    try {
        const legislationUrl = url.searchParams.get('url');
        log.info('Processing URL:', legislationUrl);
        
        if (!legislationUrl) {
            log.error('Missing URL parameter');
            return json({ error: 'URL parameter is required' }, { status: 400 });
        }

        // Construct the HTML URL instead of XML
        const htmlUrl = `${legislationUrl}/data.html`;
        log.info('Fetching HTML from:', htmlUrl);
        
        const response = await fetch(htmlUrl, {
            headers: {
                'Accept': 'application/xhtml+xml,text/html,*/*',
                'User-Agent': 'Mozilla/5.0 (compatible; LegislationFetcher/1.0)',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        });
        
        log.info('Response received:', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers)
        });

        if (!response.ok) {
            log.error('Failed to fetch HTML:', response.statusText);
            return json({ 
                error: `Failed to fetch legislation: ${response.statusText}`,
                status: response.status 
            }, { status: response.status });
        }

        const htmlContent = await response.text();
        log.info('HTML response length:', htmlContent.length);
        log.info('HTML content preview:', htmlContent.substring(0, 200));
        
        if (!htmlContent) {
            log.error('Empty response received');
            return json({ error: 'Empty response from legislation server' }, { status: 500 });
        }

        return json({ content: htmlContent });

    } catch (error) {
        log.error('Server error:', error);
        return json({ 
            error: 'Internal server error',
            details: error instanceof Error ? error.message : String(error)
        }, { status: 500 });
    }
}