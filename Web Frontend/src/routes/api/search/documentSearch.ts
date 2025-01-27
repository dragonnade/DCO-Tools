// import { supabase } from '$lib/supabaseClient';
// import type { AdvancedSearchParams, SearchResponse, SearchTerm } from '$lib/types/search';


// // // First, let's update our SearchParams interface to handle advanced searches
// // interface AdvancedSearchParams extends SearchParams {
// //   searchType: 'contains' | 'exact' | 'startsWith' | 'excludes' | 'proximity' | 'negation' | 'combined';
// //   proximityTerms?: string[];   // For proximity searches
// //   proximityDistance?: number;  // For proximity searches
// //   negationTerms?: string[];    // For negation terms
// // }

// interface ProximitySearchOptions {
//   bidirectional?: boolean;  // Search both directions?
//   includeExact?: boolean;  // Include exact matches?
// }

// function buildProximityQuery(
//   term1: string, 
//   term2: string, 
//   distance: number,
//   options: ProximitySearchOptions = { bidirectional: true, includeExact: true }
// ): string {
//   const queries: string[] = [];
  
//   // Generate queries for each distance up to the maximum
//   for (let i = 1; i <= distance; i++) {
//     // Forward direction
//     queries.push(`('${term1}' <${i}> '${term2}')`);
    
//     // Backward direction if enabled
//     if (options.bidirectional) {
//       queries.push(`('${term2}' <${i}> '${term1}')`);
//     }
//   }
  
//   // Add exact match if enabled
//   if (options.includeExact) {
//     queries.push(`('${term1}' <-> '${term2}')`);
//     if (options.bidirectional) {
//       queries.push(`('${term2}' <-> '${term1}')`);
//     }
//   }
  
//   // Combine all queries with OR operator
//   return `(${queries.join(' | ')})`;
// }


// function buildSearchQuery(searchTerms: SearchTerm[]): string {
//   const queryParts: string[] = [];

//   searchTerms.forEach(term => {
//     switch (term.type) {
//       case 'include':
//         queryParts.push(`'${term.value}'`);
//         break;

//       case 'exclude':
//         queryParts.push(`!'${term.value}'`);
//         break;

//       case 'proximity':
//         if (Array.isArray(term.value) && term.value.length === 2) {
//           console.log("Found a proximity search. Formatting search structure...")
//           queryParts.push(
//             `('${term.value[0]}' <${term.proximityDistance || 1}> '${term.value[1]}')`
//           );
//         }
//         break;
//     }
//   });

//   // Combine all parts with AND operator
//   console.log(queryParts.join(' & '))
//   return queryParts.join(' & ');
// }


// // export async function searchDocuments(params: AdvancedSearchParams): Promise<SearchResponse> {
// //   let query = supabase
// //     .from('documents')
// //     .select(`
// //       *,
// //       projects!documents_project_id_fkey(application_type)
// //     `, { count: 'exact' });

// //   // Handle different types of searches
// //   switch (params.searchType) {
// //     case 'proximity':
// //       if (params.proximityTerms && params.proximityTerms.length === 2) {
// //         // If a proximity distance is specified, use it, otherwise default to 1
// //         const distance = params.proximityDistance || 1;
// //         // Create the proximity search query
// //         // Note: we wrap each term in single quotes as required by PostgreSQL
// //         const searchQuery = `'${params.proximityTerms[0]}' <${distance}> '${params.proximityTerms[1]}'`;
// //         query = query.textSearch('title', searchQuery);
// //       }
// //       break;

// //     case 'negation':
// //       if (params.searchText && params.negationTerms) {
// //         // Create a negation search query
// //         // This will find records with searchText but NOT the negation terms
// //         const negationQuery = `'${params.searchText}' & !('${params.negationTerms.join("' | '")}')`;
// //         query = query.textSearch('title', negationQuery);
// //       }
// //       break;

// //     // Keep our existing search types
// //     case 'contains':
// //       query = query.ilike('title', `%${params.searchText}%`);
// //       break;
// //     case 'exact':
// //       query = query.eq('title', params.searchText);
// //       break;
// //     case 'startsWith':
// //       query = query.ilike('title', `${params.searchText}%`);
// //       break;
// //     case 'excludes':
// //       query = query.not('title', 'ilike', `%${params.searchText}%`);
// //       break;
// //   }

// //   // Apply date range filters if provided
// //   if (params.filters?.dateRange?.start) {
// //     query = query.gte('date_published', params.filters.dateRange.start);
// //   }
// //   if (params.filters?.dateRange?.end) {
// //     query = query.lte('date_published', params.filters.dateRange.end);
// //   }

// //   // Apply stage filters if provided
// //   if (params.filters?.stages?.length) {
// //     query = query.in('stage', params.filters.stages);
// //   }

// //   // Apply category filters if provided
// //   // Since categories are numerous, we'll use an array contains operation
// //   if (params.filters?.categories?.length) {
// //     query = query.in('category', params.filters.categories);
// //   }

// //   // Apply application type filters if provided
// //   if (params.filters?.applicationTypes?.length) {
// //     // query = query.in('project.application_type', params.filters.applicationTypes);
// //     query = query.in('projects.application_type', params.filters.applicationTypes);
// //   }

// //   // Apply pagination
// //   const from = params.page * params.pageSize;
// //   query = query
// //     .range(from, from + params.pageSize - 1)
// //     .order('date_published', { ascending: false });

// //   // Execute the query
// //   const { data, count, error } = await query;

// //   if (error) {
// //     console.error('Search error:', error);
// //     throw error;
// //   }

// //   return {
// //     documents: data,
// //     totalCount: count,
// //     currentPage: params.page,
// //     pageSize: params.pageSize
// //   };
// // }

// export async function searchDocuments(params: AdvancedSearchParams): Promise<SearchResponse> {
//   try {
//     let query = supabase
//       .from('documents')
//       .select(`
//         *,
//         projects!documents_project_id_fkey(application_type)
//       `, { count: 'exact' });
    
//     if (params.searchTerms.length > 0) {
//       const searchQueries = params.searchTerms.map(term => {
//         if (term.type === 'proximity' && Array.isArray(term.value) && term.value.length === 2) {
//           return buildProximityQuery(
//             term.value[0],
//             term.value[1],
//             term.proximityDistance || 1,
//             { bidirectional: true, includeExact: true }
//           );
//         }
//       });
//     // // Build and apply text search if there are search terms
//     // if (params.searchTerms.length > 0) {
//       const searchQuery = buildSearchQuery(params.searchTerms);
//       query = query.textSearch('title', `${searchQuery}`, {
//         config: 'english'  // Use English dictionary for better word stemming
//       });
    
//       const finalQuery = searchQueries.join(' & ');
//       query = query.textSearch('title', finalQuery, {
//         config: 'english'
//       });
//     }
//     // Apply filters if they exist
//     if (params.filters) {
//       if (params.filters.stages?.length) {
//         query = query.in('stage', params.filters.stages);
//       }

//       if (params.filters.categories?.length) {
//         query = query.in('category', params.filters.categories);
//       }

//       if (params.filters.applicationTypes?.length) {
//         query = query.in('projects.application_type', params.filters.applicationTypes);
//       }

//       if (params.filters.dateRange?.start) {
//         query = query.gte('date_published', params.filters.dateRange.start);
//       }

//       if (params.filters.dateRange?.end) {
//         query = query.lte('date_published', params.filters.dateRange.end);
//       }
//     }

//     // Apply pagination
//     const from = params.page * params.pageSize;
//     query = query
//       .range(from, from + params.pageSize - 1)
//       .order('date_published', { ascending: false });

//     // Execute query
//     const { data, count, error } = await query;

//     if (error) throw error;

//     return {
//       documents: data || [],
//       totalCount: count || 0,
//       currentPage: params.page,
//       pageSize: params.pageSize
//     };

//   }
//    catch (error) {
//     console.error('Search error:', error);
//     throw error;
//   }
// }


import { supabase } from '$lib/supabaseClient';
import type { AdvancedSearchParams, SearchResponse, SearchTerm } from '$lib/types/search';

interface ProximitySearchOptions {
  bidirectional?: boolean;  // Search both directions?
  includeExact?: boolean;  // Include exact matches?
}

function buildProximityQuery(
  term1: string, 
  term2: string, 
  distance: number,
  options: ProximitySearchOptions = { bidirectional: true, includeExact: true }
): string {
  const queries: string[] = [];
  
  // For PostgreSQL tsquery, we need to use <-> for exact adjacency
  // and <N> for distance N. To search for "within N words", we need
  // to combine multiple distance checks
  
  if (options.includeExact) {
    queries.push(`${term1} <-> ${term2}`);
    if (options.bidirectional) {
      queries.push(`${term2} <-> ${term1}`);
    }
  }
  
  // Add queries for each distance up to the maximum
  for (let i = 1; i <= distance; i++) {
    queries.push(`${term1} <${i}> ${term2}`);
    if (options.bidirectional) {
      queries.push(`${term2} <${i}> ${term1}`);
    }
  }
  
  // Combine all queries with OR operator (|)
  return `(${queries.join(' | ')})`;
}

function buildSearchQuery(searchTerms: SearchTerm[]): string {
  const queryParts: string[] = [];

  searchTerms.forEach(term => {
    switch (term.type) {
      case 'include':
        // Use :* for prefix matching
        queryParts.push(`${term.value}:*`);
        break;

      case 'exclude':
        queryParts.push(`!${term.value}:*`);
        break;

      case 'proximity':
        if (Array.isArray(term.value) && term.value.length === 2) {
          queryParts.push(
            buildProximityQuery(
              term.value[0],
              term.value[1],
              term.proximityDistance || 1,
              { bidirectional: true, includeExact: true }
            )
          );
        }
        break;
    }
  });

  // Combine all parts with AND operator (&)
  return queryParts.join(' & ');
}

export async function searchDocuments(params: AdvancedSearchParams): Promise<SearchResponse> {
  try {
    let query = supabase
      .from('documents')
      .select(`
        *,
        projects!documents_project_id_fkey(application_type)
      `, { count: 'exact' });
    
    // Build and apply text search if there are search terms
    if (params.searchTerms.length > 0) {
      const searchQuery = buildSearchQuery(params.searchTerms);
      
      // Use websearch_to_tsquery for better handling of phrases and operators
      query = query.textSearch('title', searchQuery, {
        config: 'english',  // Use English dictionary for better word stemming
        type: 'plain'      // Use plainto_tsquery for better phrase handling
      });
    }

    // Apply filters
    if (params.filters) {
      if (params.filters.stages?.length) {
        query = query.in('stage', params.filters.stages);
      }

      if (params.filters.categories?.length) {
        query = query.in('category', params.filters.categories);
      }

      if (params.filters.applicationTypes?.length) {
        query = query.in('projects.application_type', params.filters.applicationTypes);
      }

      if (params.filters.dateRange?.start) {
        query = query.gte('date_published', params.filters.dateRange.start);
      }

      if (params.filters.dateRange?.end) {
        query = query.lte('date_published', params.filters.dateRange.end);
      }
    }

    // Apply pagination
    const from = params.page * params.pageSize;
    query = query
      .range(from, from + params.pageSize - 1)
      .order('date_published', { ascending: false });

    // Execute query
    const { data, count, error } = await query;

    if (error) throw error;

    return {
      documents: data || [],
      totalCount: count || 0,
      currentPage: params.page,
      pageSize: params.pageSize
    };

  } catch (error) {
    console.error('Search error:', error);
    throw error;
  }
}