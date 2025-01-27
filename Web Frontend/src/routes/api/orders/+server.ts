import { json } from '@sveltejs/kit';
import { supabase } from '$lib/supabaseClient';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
    try {
        const { data, error } = await supabase.rpc('get_orders');
        
        if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
                status: 500
            });
        }

        return json(data);
    } catch (e) {
        return new Response(JSON.stringify({ error: 'Internal server error' }), {
            status: 500
        });
    }
};