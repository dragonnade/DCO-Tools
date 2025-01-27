// routes/api/articles/similar/+server.ts
import { json } from '@sveltejs/kit';
import { supabase } from '$lib/supabaseClient';
import type { RequestHandler } from './$types.js';

export const GET: RequestHandler = async ({ url }) => {
    try {
        const articleId = url.searchParams.get('articleId');
        
        if (!articleId) {
            return new Response(JSON.stringify({ error: 'Article ID is required' }), {
                status: 400
            });
        }

        const { data, error } = await supabase.rpc('get_future_articles', {
            article_id_param: articleId
        });

        if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
                status: 500
            });
        }

        return json(data || []);
    } catch (e) {
        return new Response(JSON.stringify({ error: 'Internal server error' }), {
            status: 500
        });
    }
};