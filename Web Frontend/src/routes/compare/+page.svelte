<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { debounce } from 'lodash';

    // Move types inside the script
    interface ComparisonResult {
        article_id: number;
        similarity: number;
        detailed_similarity: number;
        article_number: string;
        article_title: string;
        first_paragraph: string;
        category: string;
        word_count: number;
        order_id: number;
        order_name: string;
        url: string;
    }

    // Component state
    const categories = [
        'Administrative',
        'Infrastructure',
        'Rights',
        'Environmental',
        'Interpretation',
        'Operation',
        'Other'
    ];

    // Reactive variables
    let inputTitle = $state('');
    let inputText = $state('');
    let selectedCategory = $state('');
    let results = $state<ComparisonResult[]>([]);
    let isLoading = $state(false);
    let error = $state<string | null>(null);

    // Configuration parameters
    let similarityThreshold = $state(0.6);
    let wordCountRatio = $state(0.3);
    let maxResults = $state(50);

    let showAdvancedOptions = $state(false);

    // Sorting configuration
    let sortField = $state<'similarity' | 'date' | 'word_count'>('similarity');
    let sortDirection = $state<'asc' | 'desc'>('desc');

    let currentController: AbortController | null = null;

    // Sorting function
    function handleSort(field: typeof sortField) {
        if (sortField === field) {
            sortDirection = sortDirection === 'desc' ? 'asc' : 'desc';
        } else {
            sortField = field;
            sortDirection = 'desc';
        }
    }

    // Similarity formatting
    function formatSimilarity(similarity: number): string {
        return (similarity * 100).toFixed(1) + '%';
    }

    // Reactive sorting and filtering
    $effect(() => {
        if (results) {
            // Sorting logic
            results.sort((a, b) => {
                const direction = sortDirection === 'desc' ? -1 : 1;
                
                switch (sortField) {
                    case 'similarity':
                        return direction * ((b.detailed_similarity || 0) - (a.detailed_similarity || 0));
                    case 'word_count':
                        return direction * ((b.word_count || 0) - (a.word_count || 0));
                    case 'date':
                        return direction * ((b.order_id || 0) - (a.order_id || 0));
                    default:
                        return 0;
                }
            });
        }
    });

    // Filtering logic
    $effect(() => {
        if (results) {
            results = selectedCategory 
                ? results.filter(r => r && r.category === selectedCategory)
                : results;
        }
    });

    // Debounced search (commented out for now)
    const debouncedSearch = debounce(async () => {
        if (!inputText.trim()) {
            results = [];
            return;
        }

        try {
            isLoading = true;
            error = null;

            if (currentController) {
                currentController.abort();
            }
            currentController = new AbortController();

            // Fetch logic here
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: inputText,
                    similarityThreshold,
                    wordCountRatio,
                    maxResults
                }),
                signal: currentController.signal
            });

            if (!response.ok) {
                throw new Error('Failed to perform comparison');
            }

            const comparisonResults = await response.json();
            results = comparisonResults;
        } catch (e) {
            if (e instanceof Error && e.name === 'AbortError') {
                return;
            }
            error = e instanceof Error ? e.message : 'An unknown error occurred';
            console.error('Comparison error:', e);
        } finally {
            isLoading = false;
            currentController = null;
        }
    }, 500);

    onMount(() => {
        console.log('Component mounted');
    });

    onDestroy(() => {
        if (currentController) {
            currentController.abort();
        }
    });
</script>

<div class="page-container">
    <div class="content-card">
        <h1 class="page-title">Compare Text</h1>
  
        <div class="space-y-4">
            <div>
                <label for="title" class="text-sm font-medium">Title (Optional)</label>
                <input
                    id="title"
                    type="text"
                    bind:value={inputTitle}
                    placeholder="Enter article title..."
                    class="mt-1 w-full rounded-md border border-gray-300 p-2"
                />
            </div>
  
            <div>
                <label for="category" class="text-sm font-medium">Category (Optional) [Categories chosen by AI; needs sensible review]</label>
                <select
                    id="category"
                    bind:value={selectedCategory}
                    class="mt-1 w-full rounded-md border border-gray-300 p-2"
                >
                    <option value="">All Categories</option>
                    {#each categories as category}
                        <option value={category}>{category}</option>
                    {/each}
                </select>
            </div>
  
            <div>
                <label for="text" class="text-sm font-medium">Text</label>
                <textarea
                    id="text"
                    bind:value={inputText}
                    placeholder="Enter the article text to compare..."
                    class="mt-1 w-full rounded-md border border-gray-300 p-2 min-h-[200px]"
                ></textarea>
            </div>
  
            <div>
                <button
                    class="text-sm text-green-700 hover:text-green-800"
                    on:click={() => showAdvancedOptions = !showAdvancedOptions}
                >
                    {showAdvancedOptions ? 'Hide' : 'Show'} Advanced Options
                </button>
  
                {#if showAdvancedOptions}
                    <div class="mt-2 space-y-4 p-4 bg-gray-50 rounded-md">
                        <div>
                            <p>Use with caution - I'm not entirely clear on whether the ability to change these parameters will be helpful or not...</p>
                            <label for="similarity-threshold" class="text-sm font-medium">
                                Similarity Threshold ({(similarityThreshold * 100).toFixed(0)}%)
                            </label>
                            <input
                                id="similarity-threshold"
                                type="range"
                                bind:value={similarityThreshold}
                                min="0.3"
                                max="0.9"
                                step="0.05"
                                class="w-full"
                            />
                        </div>
  
                        <div>
                            <label for="word-count-ratio" class="text-sm font-medium">
                                Word Count Ratio (±{(wordCountRatio * 100).toFixed(0)}%)
                            </label>
                            <input
                                id="word-count-ratio"
                                type="range"
                                bind:value={wordCountRatio}
                                min="0.1"
                                max="0.5"
                                step="0.05"
                                class="w-full"
                            />
                        </div>
                    </div>
                {/if}

                <button class="primary-button" on:click={debouncedSearch}>
                    Submit
                </button>
            </div>
  
            {#if isLoading}
                <div class="loading-text">
                    Comparing texts... This may take a moment...
                </div>
            {:else if error}
                <div class="error-alert">
                    {error}
                </div>
            {:else if typeof filteredResults === 'undefined'}
                <div class="loading-text">Waiting for text...</div>
            {:else if filteredResults.length > 0}
                <div class="space-y-4">
                    <div class="flex justify-between items-center">
                        <h3 class="text-lg font-semibold">
                            Similar Articles ({filteredResults.length})
                        </h3>
                        
                        <div class="space-x-2">
                            <button
                                class="primary-button"
                                on:click={() => handleSort('similarity')}
                            >
                                Similarity
                                {#if sortField === 'similarity'}
                                    {sortDirection === 'desc' ? '↓' : '↑'}
                                {/if}
                            </button>
                            <button
                                class="primary-button"
                                on:click={() => handleSort('date')}
                            >
                                Date
                                {#if sortField === 'date'}
                                    {sortDirection === 'desc' ? '↓' : '↑'}
                                {/if}
                            </button>
                        </div>
                    </div>
  
                    <div class="scroll-container">
                        {#each filteredResults as result}
                            <div class="article-card">
                                <div class="flex justify-between items-start">
                                    <div>
                                        <h4 class="font-medium">
                                            {result.order_name} - Article {result.article_number}
                                        </h4>
                                        <p class="text-sm text-gray-600">{result.article_title}</p>
                                        <p class="text-sm mt-2">{result.first_paragraph}</p>
                                        {#if result.url}
                                            <a 
                                                href={result.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                class="text-green-700 hover:text-green-800 text-sm mt-2 inline-block"
                                            >
                                                View full article →
                                            </a>
                                        {/if}
                                    </div>
                                    <div class="text-right">
                                        <div class="font-bold text-lg">
                                            {formatSimilarity(result.detailed_similarity)}
                                        </div>
                                        <div class="text-sm text-gray-600">
                                            {result.word_count} words
                                        </div>
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {:else if inputText.trim()}
                <div class="text-center text-gray-600 mt-8">
                    No similar articles found
                </div>
            {/if}
        </div>
    </div>
</div>