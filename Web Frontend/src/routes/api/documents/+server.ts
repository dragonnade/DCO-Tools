// routes/api/documents/+server.ts
import { error, json } from '@sveltejs/kit';
import { supabase } from '$lib/supabaseClient';


export async function POST({ request }) {
    const { projectIds } = await request.json();
    const url = new URL(request.url);
    const pageSize = parseInt(url.searchParams.get('page_size') || '100');
    const lastId = url.searchParams.get('last_id');

    let query = supabase
        .from('documents')
        .select('*')
        .in('project_id', projectIds)
        .order('id', { ascending: true })
        .limit(pageSize);

    // Add cursor-based condition if we have a last ID
    if (lastId) {
        query = query.gt('id', lastId);
    }

    const { data, error } = await query;

    if (error) {
        return new Response(JSON.stringify({ error: error.message }), {
            status: 500
        });
    }

    return new Response(JSON.stringify({ 
        documents: data,
        stages: [...new Set(data.map(doc => doc.stage))],
        categories: [...new Set(data.map(doc => doc.category))]
    }));
}

// export async function POST({ request }) {
//     console.log('Starting POST request to /api/documents');
//     try {
//         const body = await request.json();
//         const { projectIds } = body;

//         console.log('API Request received:', {
//             projectIds,
//             timestamp: new Date().toISOString()
//         });

//         // Validate input
//         if (!Array.isArray(projectIds)) {
//             console.log('Invalid request: projectIds is not an array');
//             return json({
//                 error: true,
//                 message: 'Project IDs must be an array',
//                 documents: [],
//                 stages: [],
//                 categories: []
//             }, { status: 400 });
//         }

//         // Handle empty selection gracefully
//         if (projectIds.length === 0) {
//             console.log('No projects selected, returning empty result');
//             return json({
//                 documents: [],
//                 stages: [],
//                 categories: []
//             });
//         }

//         console.log('Fetching documents for projects:', projectIds);
        
//         // First, try to fetch just the documents without the join
//         const { data: documents, error: documentsError } = await supabase
//             .from('documents')
//             .select(`
//                 id,
//                 project_id,
//                 title,
//                 file_size,
//                 url,
//                 publishing_organization,
//                 date_published,
//                 stage,
//                 category
//             `)
//             .in('project_id', projectIds)
//             .order('date_published', { ascending: false });

//         console.log('Supabase response:', { 
//             hasData: !!documents, 
//             dataLength: documents?.length || 0,
//             error: documentsError 
//         }); // Debug log

//         if (documentsError) {
//             console.error('Error fetching documents:', documentsError);
//             throw error(500, documentsError.message);
//         }

//         // If we need project names, fetch them separately
//         if (documents && documents.length > 0) {
//             const { data: projects, error: projectsError } = await supabase
//                 .from('projects')
//                 .select('id, name')
//                 .in('id', projectIds);

//             if (projectsError) {
//                 console.error('Error fetching projects:', projectsError);
//                 throw error(500, projectsError.message);
//             }

//             // Create a map of project IDs to names
//             const projectMap = new Map(projects?.map(p => [p.id, p.name]) || []);

//             // Add project names to documents
//             const documentsWithProjects = documents.map(doc => ({
//                 ...doc,
//                 projects: {
//                     name: projectMap.get(doc.project_id) || 'Unknown Project'
//                 }
//             }));

//             return json({
//                 documents: documentsWithProjects,
//                 stages: [...new Set(documents.map(d => d.stage).filter(Boolean))],
//                 categories: [...new Set(documents.map(d => d.category).filter(Boolean))]
//             });
//         }

//         return json({
//             documents: documents || [],
//             stages: [...new Set(documents?.map(d => d.stage).filter(Boolean))],
//             categories: [...new Set(documents?.map(d => d.category).filter(Boolean))]
//         });
//     } catch (e) {
//         console.error('Detailed API error:', {
//             error: e,
//             message: e instanceof Error ? e.message : 'Unknown error',
//             stack: e instanceof Error ? e.stack : undefined
//         });
        
//         // Instead of throwing a generic error, return a JSON response with details
//         return json({
//             error: true,
//             message: e instanceof Error ? e.message : 'Unknown error',
//             documents: [],
//             stages: [],
//             categories: []
//         }, { status: 500 });
//     }
// }