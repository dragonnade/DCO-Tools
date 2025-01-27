// routes/documents/+page.ts
import { error } from '@sveltejs/kit';
import { supabase } from '$lib/supabaseClient';

export async function load() {
    console.log('Loading projects');
    
    // First, verify Supabase connection
    if (!supabase) {
        console.error('Supabase client not initialized');
        throw error(500, 'Database connection not initialized');
    }
    
    try {
        // console.log('Attempting to query projects table');
        
        // const { data: projects, error: projectsError } = await supabase
        //     .from('projects')
        //     .select('id, reference, name, application_type');

        // const { data: projects, error: projectsError } = await supabase
        //     .from('projects')
        //     .select('id, reference, name, application_type')
        //     .match('id': 
        //         supabase
        //             .from('old_documents')
        //             .select('project_id')
        //             .values('project_id')
        //     )
        //     // Ensure we don't get duplicate projects if they have multiple documents
        //     .order('name');
        
        const { data: projects, error: projectsError } = await supabase
            .rpc('get_old_doc_projects');

        if (projectsError) {
            console.error('Detailed Supabase error:', {
                message: projectsError.message,
                code: projectsError.code,
                details: projectsError.details,
                hint: projectsError.hint
            });
            throw error(500, {
                message: 'Failed to load projects',
                detail: projectsError.message
            });
        }

        const uniqueTypes = [...new Set(
            projects
                ?.filter(p => p.application_type)
                .map(p => p.application_type)
                .sort()
        )];

        return {
            projects: projects || [],
            applicationTypes: uniqueTypes
        };
    } catch (e) {
        console.error('Error in load function:', e);
        throw error(500, {
            message: 'Failed to load projects',
            detail: e instanceof Error ? e.message : 'Unknown error'
        });
    }
}