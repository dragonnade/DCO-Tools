import { json } from '@sveltejs/kit';
import { supabase } from '$lib/supabaseClient';
import type { RequestHandler } from './$types.js';

export const GET: RequestHandler = async ({ url }) => {
    try {
        const orderId = url.searchParams.get('orderId');
        
        if (!orderId) {
            return new Response(JSON.stringify({ error: 'Order ID is required' }), {
                status: 400
            });
        }

        const { data, error } = await supabase.rpc('get_articles', {
            order_id_param: orderId
        });

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