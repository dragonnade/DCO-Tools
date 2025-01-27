import { searchDocuments } from '../api/search/documentSearch';

// export async function runSearchTests() {
//     console.log('Starting search tests...');



//     // Test 2: Negation search example
//     try {
//         console.log('Running Test 2: Negation search');
//         const negationSearchResult = await searchDocuments({
//             searchText: 'development',
//             searchType: 'negation',
//             negationTerms: ['draft', 'preliminary'],
//             page: 0,
//             pageSize: 10
//         });
//         console.log('Negation Search Results:', negationSearchResult);
//     } catch (error) {
//         console.error('Negation search test failed:', error);
//     }

//     // Test 3: Search with filters
//     try {
//         console.log('Running Test 3: Search with filters');
//         const filteredSearchResult = await searchDocuments({
//             searchText: 'order',
//             searchType: 'contains',
//             filters: {
//                 stages: ['Examination'],
//                 dateRange: {
//                     start: '2023-01-01',
//                     end: '2024-01-01'
//                 }
//             },
//             page: 0,
//             pageSize: 100
//         });
//         console.log('Test 3 Results:', filteredSearchResult);
//     } catch (error) {
//         console.error('Test 3 failed:', error);
//     }
// }

export async function runSearchTests() {
    console.log('Starting advanced search tests...');

    // Test 1: Basic proximity search (within 2 words)
    try {
        console.log('\nTest 1: Basic proximity - "development" within 2 words of "consent"');
        const test1 = await searchDocuments({
            searchTerms: [{
                type: 'proximity',
                value: ['development', 'consent'],
                proximityDistance: 2
            }],
            page: 0,
            pageSize: 10
        });
        console.log('Results count:', test1.totalCount);
        console.log('Sample matches:', test1.documents.slice(0, 3).map(doc => doc.title));
    } catch (error) {
        console.error('Test 1 failed:', error);
    }

    // Test 2: Larger distance (within 5 words)
    try {
        console.log('\nTest 2: Larger distance - "development" within 5 words of "order"');
        const test2 = await searchDocuments({
            searchTerms: [{
                type: 'proximity',
                value: ['development', 'order'],
                proximityDistance: 5
            }],
            page: 0,
            pageSize: 10
        });
        console.log('Results count:', test2.totalCount);
        console.log('Sample matches:', test2.documents.slice(0, 3).map(doc => doc.title));
    } catch (error) {
        console.error('Test 2 failed:', error);
    }

    // Test 3: Proximity search with filters
    try {
        console.log('\nTest 3: Proximity search with filters');
        const test3 = await searchDocuments({
            searchTerms: [{
                type: 'proximity',
                value: ['development', 'consent'],
                proximityDistance: 3
            }],
            filters: {
                stages: ['Examination'],
                dateRange: {
                    start: '2023-01-01',
                    end: '2024-12-31'
                }
            },
            page: 0,
            pageSize: 10
        });
        console.log('Results count:', test3.totalCount);
        console.log('Sample matches:', test3.documents.slice(0, 3).map(doc => doc.title));
    } catch (error) {
        console.error('Test 3 failed:', error);
    }

    // Test 4: Multiple proximity terms combined
    try {
        console.log('\nTest 4: Multiple proximity terms');
        const test4 = await searchDocuments({
            searchTerms: [
                {
                    type: 'proximity',
                    value: ['development', 'consent'],
                    proximityDistance: 2
                },
                {
                    type: 'proximity',
                    value: ['order', 'tracked'],
                    proximityDistance: 3
                }
            ],
            page: 0,
            pageSize: 10
        });
        console.log('Results count:', test4.totalCount);
        console.log('Sample matches:', test4.documents.slice(0, 3).map(doc => doc.title));
    } catch (error) {
        console.error('Test 4 failed:', error);
    }

    // Test 5: Proximity search with common words
    try {
        console.log('\nTest 5: Proximity with common words');
        const test5 = await searchDocuments({
            searchTerms: [{
                type: 'proximity',
                value: ['application', 'form'],
                proximityDistance: 2
            }],
            page: 0,
            pageSize: 10
        });
        console.log('Results count:', test5.totalCount);
        console.log('Sample matches:', test5.documents.slice(0, 3).map(doc => doc.title));
    } catch (error) {
        console.error('Test 5 failed:', error);
    }

    // Test 6: Proximity search with exact matches included
    try {
        console.log('\nTest 6: Proximity search including exact matches');
        const test6 = await searchDocuments({
            searchTerms: [{
                type: 'proximity',
                value: ['environmental', 'statement'],
                proximityDistance: 1
            }],
            page: 0,
            pageSize: 10
        });
        console.log('Results count:', test6.totalCount);
        console.log('Sample matches:', test6.documents.slice(0, 3).map(doc => doc.title));
    } catch (error) {
        console.error('Test 6 failed:', error);
    }
}