import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { supabase } from '$lib/supabaseClient';

interface ComparisonRequest {
    text: string;
    candidates: any[];
    similarityThreshold: number;
    wordCountRatio: number;
    maxResults: number;  // Added this as it's used in the code
}

interface ComparisonResult {
    similarity: number;
    article_number: string;
    article_title: string;
    first_paragraph: string;
    category: string;
    word_count: number;
    url: string;
    order_name: string;
    order_id: string;
}

// The Levenshtein distance algorithm helps us calculate text similarity
// by counting the minimum number of single-character edits required
// to change one string into another
function levenshteinDistance(s1: string, s2: string): number {
    // Create a matrix to store our intermediate calculations
    const m = s1.length;
    const n = s2.length;
    const dp: number[][] = Array.from({ length: m + 1 }, () => 
        Array(n + 1).fill(0)
    );

    // Initialize the first row and column
    // These represent the distance from an empty string
    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;

    // Fill in the rest of the matrix
    // For each position, we take the minimum of:
    // 1. Delete a character (cost of 1)
    // 2. Insert a character (cost of 1)
    // 3. Substitute a character (cost of 1 if characters are different, 0 if same)
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            dp[i][j] = Math.min(
                dp[i-1][j] + 1,  // deletion
                dp[i][j-1] + 1,  // insertion
                dp[i-1][j-1] + (s1[i-1] !== s2[j-1] ? 1 : 0)  // substitution
            );
        }
    }

    return dp[m][n];
}

// export const POST: RequestHandler = async ({ request }) => {
//     try {
//         const body = await request.json() as ComparisonRequest;
//         const { text, similarityThreshold, wordCountRatio, maxResults } = body;

//         const { data: vectorMatches, error: vectorError } = await supabase
//             .rpc('find_similar_articles', {
//                 search_text: text,
//                 similarity_threshold: similarityThreshold,
//                 word_count_ratio: wordCountRatio,
//                 max_results: maxResults
//             });

//         if (vectorError) {
//             throw new Error(`Vector similarity search failed: ${vectorError.message}`);
//         }

//         if (!vectorMatches || vectorMatches.length === 0) {
//             return json([]);
//         }

//         const detailedResults = await Promise.all(
//             vectorMatches.map(async (candidate: any) => {
//                 try {
//                     const { data: articleData, error: articleError } = await supabase
//                         .from('articles')
//                         .select('article_text')
//                         .eq('article_id', candidate.article_id)
//                         .single();

//                     if (articleError) {
//                         console.error(`Error fetching article ${candidate.article_id}:`, articleError);
//                         return null;
//                     }

//                     const normalizedText = text.toLowerCase().trim();
//                     const normalizedArticleText = Array.isArray(articleData.article_text) 
//                         ? articleData.article_text.join(' ') 
//                         : articleData.article_text;
                    
//                     const distance = levenshteinDistance(
//                         normalizedText,
//                         normalizedArticleText.toLowerCase().trim()
//                     );
                    
//                     const maxLength = Math.max(
//                         normalizedText.length,
//                         normalizedArticleText.length
//                     );
//                     const detailedSimilarity = 1 - (distance / maxLength);

//                     return {
//                         ...candidate,
//                         detailed_similarity: detailedSimilarity
//                     };
//                 } catch (error) {
//                     console.error('Error processing article:', error);
//                     return null;
//                 }
//             })
//         );

//         const finalResults = detailedResults
//             .filter((result): result is NonNullable<typeof result> => 
//                 result !== null && result.detailed_similarity >= similarityThreshold)
//             .sort((a, b) => b.detailed_similarity - a.detailed_similarity);

//         return json(finalResults);
//     } catch (err) {
//         const error = err as Error;
//         console.error('API error:', error);
//         return json(
//             { error: 'Internal server error', details: error.message },
//             { status: 500 }
//         );
//     }
// };

export const POST: RequestHandler = async ({ request }) => {
    console.log('Received comparison request');
    try {
        const body = await request.json();
        console.log('Request body:', body);

        const { data, error: vectorError } = await supabase
            .rpc('find_similar_articles', {
                search_text: body.text,
                similarity_threshold: body.similarityThreshold,
                word_count_ratio: body.wordCountRatio,
                max_results: body.maxResults
            });

        if (vectorError) {
            console.error('Supabase RPC error:', vectorError);
            throw new Error(`Vector similarity search failed: ${vectorError.message}`);
        }

        console.log('Comparison completed successfully');
        return json(data || []);
    } catch (err) {
        console.error('API error details:', {
            name: err.name,
            message: err.message,
            stack: err.stack
        });
        return json(
            { error: 'Internal server error', details: err.message },
            { status: 500 }
        );
    }
};