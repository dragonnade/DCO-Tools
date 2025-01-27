<!-- src/routes/test/+page.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    // import { diff } from 'diff-match-patch-es';
    import { 
        diff,                    // The main diff function (aliased from diffMain)
        diffCleanupSemantic,     // For semantic-based cleanup of diffs
        diffCleanupEfficiency,   // For efficiency-based cleanup of diffs
    } from 'diff-match-patch-es';

    let isLoading = false;
    let error: string | null = null;
    let diffContent: string | null = null;
    let debugInfo: string = '';

    const originalUrl = 'https://www.legislation.gov.uk/uksi/2024/1014/article/3/made';
    const comparisonUrl = 'https://www.legislation.gov.uk/uksi/2020/1075/article/3/made';

    // Store the full text for position mapping
    let baseText: string = '';
    let currentDiffPos: number = 0;

    function extractStructuredContent(html: string): {
        element: HTMLElement;
        textMap: Map<Node, string>;
        extractedText: string;
    } {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const textMap = new Map<Node, string>();
        
        const articleBody = doc.querySelector('article.act .body');
        if (!articleBody) {
            throw new Error('Could not find article body content');
        }

        function walkNode(node: Node): string {
            if (!node) return '';

            if (node instanceof Element) {
                if (node.classList.contains('meta') || 
                    node.classList.contains('footnotes')) {
                    return '';
                }
            }

            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent?.trim() || '';
                if (text) {
                    textMap.set(node, text);
                    debugInfo += `Text node: "${text}"\n`;
                }
                return text;
            }
            
            if (node.nodeType === Node.ELEMENT_NODE) {
                const texts: string[] = [];
                node.childNodes.forEach(child => {
                    const childText = walkNode(child);
                    if (childText) {
                        texts.push(childText);
                    }
                });
                return texts.join(' ');
            }
            
            return '';
        }

        const extractedText = walkNode(articleBody);
        return {
            element: articleBody as HTMLElement,
            textMap,
            extractedText
        };
    }

    function applyDiffToStructure(
        baseElement: HTMLElement,
        textMap: Map<Node, string>,
        differences: Array<[number, string]>
    ): HTMLElement {
        const result = baseElement.cloneNode(true) as HTMLElement;
        
        // Create a new map that uses text content as the key
        const textToOriginalMap = new Map<string, string>();
        textMap.forEach((text, node) => {
            textToOriginalMap.set(text, text);
        });

        function walkAndUpdate(node: Node) {
            const nodeText = node.textContent?.trim() || '';
            debugInfo += `Processing node: "${nodeText}"\n`;
            
            if (node.nodeType === Node.TEXT_NODE && textToOriginalMap.has(nodeText)) {
                debugInfo += `Found matching text node: "${nodeText}"\n`;
                
                let newContent = '';
                let currentPos = 0;
                let lastPos = 0;
                
                // Find the position of this text in the complete document
                const fullText = Array.from(textMap.values()).join(' ');
                const nodeStart = fullText.indexOf(nodeText);
                
                if (nodeStart !== -1) {
                    debugInfo += `Node text found at position ${nodeStart}\n`;
                    
                    // Process each difference that affects this node
                    for (const [type, text] of differences) {
                        const diffStart = currentPos;
                        const diffEnd = diffStart + text.length;
                        
                        // Check if this diff overlaps with our node
                        if (diffEnd > nodeStart && diffStart < nodeStart + nodeText.length) {
                            // Calculate the relative positions within this node
                            const relStart = Math.max(0, diffStart - nodeStart);
                            const relEnd = Math.min(nodeText.length, diffEnd - nodeStart);
                            
                            // Add any unchanged text before this diff
                            if (relStart > lastPos) {
                                newContent += nodeText.slice(lastPos, relStart);
                            }
                            
                            // Add the diff text with appropriate styling
                            const diffText = text.slice(
                                Math.max(0, nodeStart - diffStart),
                                Math.min(text.length, nodeStart + nodeText.length - diffStart)
                            );
                            
                            if (type !== 0) {
                                const className = type === 1 ? 'addition' : 'deletion';
                                newContent += `<span class="content ${className}">${diffText}</span>`;
                                debugInfo += `Applied ${className} to: "${diffText}"\n`;
                            } else {
                                newContent += diffText;
                            }
                            
                            lastPos = relEnd;
                        }
                        currentPos += text.length;
                    }
                    
                    // Add any remaining unchanged text
                    if (lastPos < nodeText.length) {
                        newContent += nodeText.slice(lastPos);
                    }
                    
                    // Only replace if we actually made changes
                    if (newContent !== nodeText) {
                        const wrapper = document.createElement('span');
                        wrapper.className = 'diff-content-wrapper';
                        wrapper.innerHTML = newContent || nodeText;
                        node.parentNode?.replaceChild(wrapper, node);
                        debugInfo += `Updated node content\n`;
                    }
                }
            } else {
                node.childNodes.forEach(walkAndUpdate);
            }
        }

        walkAndUpdate(result);
        return result;
    }

    async function fetchLegislationContent(url: string): Promise<string> {
        const response = await fetch(`/api/legislation?url=${encodeURIComponent(url)}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch legislation: ${response.statusText}`);
        }
        const data = await response.json();
        return data.content;
    }

    async function performComparison() {
        isLoading = true;
        error = null;
        debugInfo = '';
        
        try {
            // First fetch both documents
            console.log('Fetching content...');
            const originalContent = await fetchLegislationContent(originalUrl);
            const comparisonContent = await fetchLegislationContent(comparisonUrl);

            // Extract structured content from both documents
            const originalDoc = extractStructuredContent(originalContent);
            const comparisonDoc = extractStructuredContent(comparisonContent);

            // Store the base text for position mapping later
            baseText = originalDoc.extractedText;

            debugInfo += `\nOriginal text length: ${originalDoc.extractedText.length}\n`;
            debugInfo += `Comparison text length: ${comparisonDoc.extractedText.length}\n`;

            // Stage 1: Compute the initial raw differences
            // This gives us the most granular comparison possible
            const rawDiffs = diff(originalDoc.extractedText, comparisonDoc.extractedText);
            debugInfo += `\nInitial raw differences computed: ${rawDiffs.length}\n`;

            // Stage 2: Apply semantic cleanup
            // This groups changes that are semantically related
            // For example, changes that form complete words or phrases
            diffCleanupSemantic(rawDiffs);
            debugInfo += `\nAfter semantic cleanup: ${rawDiffs.length} differences\n`;

            // Stage 3: Apply efficiency cleanup with our custom parameters
            // This is where we control how aggressively changes are grouped
            diffCleanupEfficiency(rawDiffs, {
                // Higher value means more aggressive grouping of changes
                diffEditCost: 15,
                // Lower threshold makes matching more strict
                matchThreshold: 0.5,
                // Increased distance allows looking further for better matches
                matchDistance: 1500,
                // More time for complex legislation text
                diffTimeout: 2
            });
            debugInfo += `\nAfter efficiency cleanup: ${rawDiffs.length} differences\n`;

            // Log some sample diffs to help with debugging
            debugInfo += `\nFirst few processed diffs:\n`;
            rawDiffs.slice(0, 5).forEach(([type, text]) => {
                const typeLabel = type === 1 ? 'INSERT' : type === -1 ? 'DELETE' : 'EQUAL';
                debugInfo += `Type: ${typeLabel}, Text: "${text.slice(0, 50)}..."\n`;
            });

            // Stage 4: Apply the processed diffs to the HTML structure
            const diffResult = applyDiffToStructure(
                originalDoc.element,
                originalDoc.textMap,
                rawDiffs
            );

            // Store the final HTML result
            diffContent = diffResult.outerHTML;
            
        } catch (e) {
            error = e instanceof Error ? e.message : 'An error occurred';
            console.error('Error in comparison:', e);
        } finally {
            isLoading = false;
        }
    }



    onMount(() => {
        performComparison();
    });
</script>


<svelte:head>
    <style>
        .diff-content-wrapper {
            display: inline !important;
        }
        
        .content.addition {
            background-color: #e6ffe6 !important;
            text-decoration: underline !important;
            color: #006400 !important;
            display: inline !important;
            padding: 0.1em 0 !important;
            margin: 0 !important;
        }
        
        .content.deletion {
            background-color: #ffe6e6 !important;
            text-decoration: line-through !important;
            color: #640000 !important;
            display: inline !important;
            padding: 0.1em 0 !important;
            margin: 0 !important;
        }

        /* More specific selectors to override existing styles */
        article.act .body span.diff-content-wrapper,
        article.act .body span.content.addition,
        article.act .body span.content.deletion {
            display: inline !important;
            text-decoration: inherit !important;
        }

        /* Reset any problematic inherited styles */
        article.act .body [class*="content"] {
            all: revert;
            display: inline !important;
        }
    </style>
</svelte:head>

<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold mb-4">Redline Comparison Test</h1>
    
    {#if isLoading}
        <div class="bg-blue-100 p-4 rounded">Loading comparison...</div>
    {:else if error}
        <div class="bg-red-100 p-4 rounded">Error: {error}</div>
    {:else}
        <div class="space-y-4">
            {#if diffContent}
                <div class="bg-white p-6 rounded shadow">
                    <h2 class="text-xl font-semibold mb-4">Comparison Result</h2>
                    <div class="diff-content prose max-w-none">
                        {@html diffContent}
                    </div>
                </div>
            {/if}
            
            <div class="bg-gray-50 p-4 rounded">
                <h3 class="font-semibold mb-2">Debug Information</h3>
                <pre class="whitespace-pre-wrap text-sm">{debugInfo}</pre>
            </div>
        </div>
    {/if}
</div>