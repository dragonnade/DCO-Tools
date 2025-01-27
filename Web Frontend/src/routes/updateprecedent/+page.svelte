 <!-- * Development Consent Order (DCO) Analysis System
 * 
 * This Svelte-based application provides a hierarchical interface for exploring and analyzing
 * Development Consent Orders, which are specialized types of Statutory Instruments used in
 * infrastructure planning and development in the UK.
 * 
 * The system follows a three-level navigation structure:
 * 1. Orders grouped by year
 * 2. Articles within a selected Order
 * 3. Similar Articles comparison view -->

<script lang="ts">
    import { onMount } from 'svelte';
    // Import commented out for future redline comparison feature
    // import RedlineComparison from '$lib/components/RedlineComparison.svelte';

    /**
     * Core data types representing the DCO structure
     */
    
    // Represents a single Development Consent Order
    type Order = {
        id: string;
        name: string;  // Order identifier
        si: string;    // Statutory Instrument reference
    };

    // Groups Orders by year for temporal navigation
    type YearlyOrders = {
        year: number;
        orders: Order[];
    };

    // Represents an individual article within a DCO
    type Article = {
        article_id: string;
        article_number: string;      // Article reference number
        article_title: string;
        category: string;            // Classification category
        word_count: number;
        first_paragraph: string;     // Preview text
        url: string;                 // Link to legislation.gov.uk
        order_name?: string;
    };

    // Represents an article found through similarity matching
    type SimilarArticle = {
        similarity: number;          // Pre-computed similarity percentage from Supabase
        article_number: string;
        article_title: string;
        first_paragraph: string;
        category: string;
        word_count: number;
        url: string;                 // External legislation.gov.uk URL
        order_name: string;
        order_id: string;
        similarity_id: string;
    };

    // Future feature: Types for redline comparison functionality
    // type ComparisonSelection = {
    //     articleId: string;
    //     orderName: string;
    //     articleTitle: string;
    //     orderOfSelection: number;
    //     url: string;
    // };

    /**
     * State Management
     * The application uses multiple state variables to handle the hierarchical navigation
     * and data loading states
     */

    // Order listing state
    let orders: YearlyOrders[] = [];
    let isLoading = false;
    let error: string | null = null;

    // Article view state
    let selectedOrderId: string | null = null;
    let articles: Article[] = [];
    let showingArticles = false;

    // Similar articles comparison state
    let similarArticles: SimilarArticle[] = [];
    let showingSimilarArticles = false;
    let selectedArticleId: string | null = null;
    let selectedArticleDetails: Article | null = null;

    // Future feature: Redline comparison state
    // let redlineSelections = []
    // let redlineGroup = [{selectedArticleId},{redlineSelections}]
    // let selectedComparisons: ComparisonSelection[] = [];
    // let showingComparison = false;

    /**
     * UI Navigation Helpers
     */
    
    // Maintains references to year headers for smooth scrolling
    let yearElements: (HTMLElement | null)[] = [];

    /**
     * Scrolls the view to the specified year's section
     * Provides smooth navigation in the chronological view
     */
    function scrollToYear(year: number) {
        const index = orders.findIndex(group => group.year === year);
        if (index >= 0 && yearElements[index]) {
            yearElements[index]?.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }
    }

    /**
     * Truncates text for preview displays while maintaining word boundaries
     * Ensures consistent and readable previews of article content
     */
    function truncateText(text: string, maxLength: number = 80): string {
        if (!text || text.length <= maxLength) {
            return text;
        }
        let truncated = text.slice(0, maxLength);
        let lastSpaceIndex = truncated.lastIndexOf(' ');
        if (lastSpaceIndex === -1) {
            return truncated + '...';
        }
        return truncated.slice(0, lastSpaceIndex) + '...';
    }

    /**
     * Data Fetching Functions
     * These functions handle API communication and state updates
     */

    /**
     * Fetches all Development Consent Orders grouped by year
     * Initializes the primary navigation view
     */
    async function fetchOrders() {
        try {
            isLoading = true;
            error = null;
            
            const response = await fetch('/api/orders');
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch orders');
            }

            orders = data || [];
        } catch (e) {
            error = e.message;
            console.error('Error fetching orders:', e);
        } finally {
            isLoading = false;
        }
    }

    /**
     * Fetches articles for a specific Development Consent Order
     * Transitions the view to article listing
     */
    async function fetchArticles(orderId: string) {
        try {
            isLoading = true;
            error = null;
            
            const response = await fetch(`/api/articles?orderId=${orderId}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch articles');
            }

            articles = data || [];
            showingArticles = true;
            selectedOrderId = orderId;
        } catch (e) {
            error = e.message;
            console.error('Error fetching articles:', e);
        } finally {
            isLoading = false;
        }
    }

    /**
     * Fetches similar articles based on pre-computed similarity scores
     * Enables comparative analysis of DCO articles
     */
    async function fetchSimilarArticles(articleId: string, articleDetails: Article) {
        try {
            isLoading = true;
            error = null;
            
            const response = await fetch(`/api/articles/future_similar?articleId=${articleId}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch similar articles');
            }

            similarArticles = data || [];
            showingSimilarArticles = true;
            selectedArticleId = articleId;
            selectedArticleDetails = articleDetails;
        } catch (e) {
            error = e.message;
            console.error('Error fetching similar articles:', e);
        } finally {
            isLoading = false;
        }
    }

    /**
     * Navigation state management
     * Handles hierarchical back navigation through the application views
     */
    function backToOrders() {
        if (showingSimilarArticles) {
            // Reset similarity comparison view state
            showingSimilarArticles = false;
            selectedArticleId = null;
            selectedArticleDetails = null;
            similarArticles = [];
            showingArticles = true;
        } else {
            // Reset article listing view state
            showingArticles = false;
            selectedOrderId = null;
            articles = [];
        }
    }

    // Initialize the application by fetching orders on mount
    onMount(() => {
        fetchOrders();
    })
</script>

<!-- 
    Main Application Template
    The UI is structured as a single-page application with conditional rendering
    based on the current navigation state
-->
<div class="page-container">
    <div class="content-card">
        <h1 class="page-title">
            Precedent Finder
        </h1>
        <div class="sm">
            <p text-xs>This tool shows how a particular article is precedent for articles in later DCOs. To find the precedent for a particular article, please use the <a underline href="/precedent">Precedent Finder</a></p>
        </div>

        <!-- Similar Articles View -->
        {#if showingSimilarArticles}
            <div class="mb-4">
                <button
                    class="primary-button"
                    on:click={backToOrders}
                >
                    Back to Articles
                </button>
            </div>

            <!-- Display selected article details -->
            <div class="article-card mb-6 bg-green-50 border-green-200">
                <div class="mt-2">
                    <p class="font-semibold text-center text-lg">
                        Similar Articles to:<br>
                        <span class="italic">{selectedArticleDetails.order_name}</span>
                    </p>
                    <p class="font-semibold text-lg">
                        {selectedArticleDetails.article_number}. {selectedArticleDetails.article_title}
                    </p>
                    <p class="text-sm mt-2">{selectedArticleDetails.first_paragraph}</p>
                    {#if selectedArticleDetails.url}
                        <a href={selectedArticleDetails.url} 
                           target="_blank" 
                           class="text-green-700 hover:text-green-800 text-sm mt-2 inline-block">
                            View full article →
                        </a>
                    {/if}
                </div>
            </div>

            <!-- Similar articles listing -->
            <div class="scroll-container">
                <div class="space-y-4">
                    {#each similarArticles as article}
                        <div class="article-card">
                            <div class="flex justify-between items-start">
                                <h3 class="text-md">
                                    {article.order_name}
                                </h3>
                                <span class="text-sm text-green-700 clear-left">
                                    Similarity: {(article.similarity).toFixed(1)}%
                                </span>
                            </div>
                            <p class="font-semibold italic">{article.article_number}. {article.article_title}</p>
                            <p class="text-xs mt-2">{truncateText(article.first_paragraph)}</p>
                            <div class="mt-2 flex justify-between items-center text-sm">
                                {#if article.url}
                                    <a href={article.url} 
                                       target="_blank" 
                                       class="text-green-700 hover:text-green-800">
                                        View full article →
                                    </a>
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
            </div>

        <!-- Articles View -->
        {:else if showingArticles}
            <div class="mb-4">
                <button
                    class="primary-button"
                    on:click={backToOrders}
                >
                    Back to Orders
                </button>
            </div>
            <div class="scroll-container">
                <div class="space-y-4">
                    {#each articles as article}
                        <button
                            class="article-card w-full text-left"
                            on:click={() => fetchSimilarArticles(article.article_id, article)}
                            on:keydown={(e) => e.key === 'Enter' && fetchSimilarArticles(article.article_id, article)}
                            role="button"
                            aria-label="View similar articles for {article.article_title}"
                        >
                            <h3 class="font-semibold text-md">
                                {article.article_number}. {article.article_title}
                                {#if article.url}
                                    <a href={article.url} 
                                    target="_blank" 
                                    class="text-green-700 hover:text-green-800 text-sm mt-2 inline-block"
                                    on:click|stopPropagation
                                    >
                                        View full article →
                                    </a>
                                {/if}
                            </h3>
                            <p class="text-xs mt-2">{truncateText(article.first_paragraph)}</p>
                        </button>
                    {/each}
                </div>
            </div>

        <!-- Orders View (Default) -->
        {:else}
            <div class="mb-4">
                <button
                    class="primary-button"
                    on:click={fetchOrders}
                    disabled={isLoading}
                >
                    {isLoading ? 'Loading...' : 'Get Orders'}
                </button>
            </div>

            <!-- Error handling -->
            {#if error}
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            {/if}

            {#if isLoading}
                <div class="loading-text">Loading...</div>
            {:else}
                <!-- Year navigation and order listing -->
                <div class="flex flex-col space-y-6">
                    <div class="year-navigation">
                        <h3 class="text-lg font-semibold mb-2">Available Years</h3>
                        <div class="flex flex-wrap gap-3">
                            {#each orders as yearGroup}
                                <button 
                                    class="px-2 py-1 bg-white hover:bg-green-700 hover:text-white rounded-md shadow-sm border border-gray-300 text-sm"
                                    on:click={() => scrollToYear(yearGroup.year)}
                                >
                                    {yearGroup.year}
                                </button>
                            {/each}
                        </div>
                    </div>
                    <div class="scroll-container">
                        {#each orders as yearGroup, index}
                            <div class="mb-4">
                                <h2
                                    class="text-xl font-semibold mb-2"
                                    bind:this={yearElements[index]}
                                >
                                    {yearGroup.year}
                                </h2>
                                <div class="year-grid">
                                    {#each yearGroup.orders as order}
                                        <button
                                            class="order-card w-full text-left"
                                            on:click={() => fetchArticles(order.id)}
                                            on:keydown={(e) => e.key === 'Enter' && fetchArticles(order.id)}
                                            role="button"
                                            aria-label="View articles for order {order.name}"
                                        >
                                            <p class="order-text">{order.name}/{order.si}</p>
                                        </button>
                                    {/each}
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        {/if}
    </div>
</div>