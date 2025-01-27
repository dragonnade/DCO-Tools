<script lang="ts">
  import { diff } from 'diff-match-patch-es';
  import type { ComparisonSelection } from '$lib/types/comparison';

  export let selectedArticle: any;
  export let comparisons: ComparisonSelection[] = [];
  
  let isLoading = true;
  let baseContent: string = '';
  let comparisonContents: Record<string, string> = {};
  let diffResults: Record<string, HTMLElement[]> = {};

  // Helper function to extract text content from legislation HTML
  function extractStructuredContent(html: string): {element: HTMLElement, textMap: Map<Node, string>, extractedText: string} {
    if (!html) {
      throw new Error('Empty HTML content provided');
    }
    
    console.log('Processing HTML content of length:', html.length);
    
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const textMap = new Map<Node, string>();
    
    const article = doc.querySelector('article.act');
    const bodyContent = article?.querySelector('.body');
    
    if (!bodyContent) {
      throw new Error('Invalid legislation HTML structure: Could not find .body element');
    }

    // Add null checks in walkNode
    function walkNode(node: Node): string {
      if (!node) {
        return '';
      }
      // Skip metadata and footnotes
      if (node instanceof Element) {
        if (node.classList.contains('meta') || 
            node.classList.contains('footnotes')) {
          return '';
        }
        
        // Special handling for different content types
        if (node.classList.contains('num') || 
            node.classList.contains('heading')) {
          const text = node.textContent?.trim() || '';
          if (text) {
            textMap.set(node, text);
          }
          return text;
        }
      }

      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent?.trim() || '';
        if (text) {
          textMap.set(node, text);
        }
        return text;
      }
      
      if (node.nodeType === Node.ELEMENT_NODE) {
        const texts = [];
        for (const child of node.childNodes) {
          const childText = walkNode(child);
          if (childText) {
            texts.push(childText);
          }
        }
        return texts.join(' ');
      }
      
      return '';
    }

    const extractedText = walkNode(bodyContent);
    
    if (!extractedText) {
      throw new Error('No text content could be extracted from the document');
    }

    console.log('Text extraction complete:', {
      textLength: extractedText.length,
      mapSize: textMap.size,
      textStart: extractedText.substring(0, 100),
      mapEntries: Array.from(textMap.entries()).length
    });

    return {
      element: bodyContent as HTMLElement,
      textMap,
      extractedText
    };
  }

  // Function to apply diff results back to HTML structure
  function applyDiffToStructure(
    baseElement: HTMLElement,
    textMap: Map<Node, string>,
    differences: Array<[number, string]>
  ): HTMLElement {
    const result = baseElement.cloneNode(true) as HTMLElement;
    let currentPos = 0;


    function updateTextNode(node: Node) {
      const originalText = textMap.get(node);
      if (!originalText) return;

      const textStart = currentPos;
      const textEnd = textStart + originalText.length;
      let newHtml = '';
      let currentDiffPos = 0;
      let currentTextPos = 0;

      for (const [type, text] of differences) {
          const diffStart = currentDiffPos;
          const diffEnd = diffStart + text.length;
          
          // Skip diffs before this text node
          if (diffEnd <= textStart) {
              currentDiffPos += text.length;
              continue;
          }
          
          // Stop if we've passed this text node
          if (diffStart >= textEnd) {
              break;
          }

          // Calculate overlap with this text node
          const overlapStart = Math.max(diffStart, textStart);
          const overlapEnd = Math.min(diffEnd, textEnd);
          const overlapText = text.slice(
              Math.max(0, textStart - diffStart),
              text.length - Math.max(0, diffEnd - textEnd)
          );

          if (overlapStart > currentTextPos) {
              // Add unchanged text before this diff
              newHtml += originalText.slice(currentTextPos, overlapStart - textStart);
          }

          // Add the diff with appropriate styling
          const className = type === 0 ? 'unchanged' :
                          type === 1 ? 'content addition' :
                          'content deletion';
          newHtml += `<span class="${className}">${overlapText}</span>`;
          
          currentTextPos = overlapEnd - textStart;
          currentDiffPos += text.length;
      }

      // Add any remaining unchanged text
      if (currentTextPos < originalText.length) {
          newHtml += originalText.slice(currentTextPos);
      }

      // Create a wrapper that preserves inline display
      const wrapper = document.createElement('span');
      wrapper.className = 'diff-content-wrapper';
      wrapper.innerHTML = newHtml;
      node.parentNode?.replaceChild(wrapper, node);
      currentPos += originalText.length;
  }

    function walkAndUpdate(node: Node) {
      if (node.nodeType === Node.TEXT_NODE && textMap.has(node)) {
        updateTextNode(node);
      } else {
        node.childNodes.forEach(walkAndUpdate);
      }
    }

    walkAndUpdate(result);
    return result;
  }

  async function loadAllContent() {
    console.log('Starting content load');
    isLoading = true;
    
    try {
      if (!selectedArticle?.url) {
        console.error('No URL for selected article:', selectedArticle);
        throw new Error('No URL for selected article');
      }

      // Load base content
      console.log('Fetching base content from:', selectedArticle.url);
      const baseResponse = await fetchLegislationContent(selectedArticle.url);
      console.log('Base content length:', baseResponse?.length);
      
      // Store all the base content information
      const baseContentInfo = extractStructuredContent(baseResponse);
      const { element: baseElement, textMap: baseTextMap, extractedText: baseText } = baseContentInfo;
      
      baseContent = baseElement.innerHTML;
      console.log('Processed base content length:', baseContent.length);

      // Process each comparison
      for (const comparison of comparisons) {
        if (!comparison.url) {
          console.log('Skipping comparison without URL:', comparison);
          continue;
        }
        
        try {
          console.log('Processing comparison:', comparison.articleId);
          
          // First fetch and process the comparison content
          const comparisonResponse = await fetchLegislationContent(comparison.url);
          console.log('Comparison content length:', comparisonResponse?.length);
          
          const { element: comparisonElement, textMap: comparisonTextMap, extractedText: comparisonText } = 
            extractStructuredContent(comparisonResponse);

          // Now we can safely log the comparison details
          console.log('Computing diff with texts:', {
            baseTextLength: baseText?.length,
            comparisonTextLength: comparisonText?.length,
            baseTextValid: typeof baseText === 'string',
            comparisonTextValid: typeof comparisonText === 'string',
            baseTextSample: baseText?.substring(0, 100),
            comparisonTextSample: comparisonText?.substring(0, 100)
          });

          if (!baseText || !comparisonText) {
            throw new Error('Missing text content for diff computation');
          }

          const differences = diff(baseText, comparisonText, {
            diffTimeout: 1,    // Time limit for computation in seconds
            editCost: 4,       // Cost of an empty edit operation
            cleanup: true      // Automatically clean up the diff output
          });

          // Add validation of diff results
          if (!Array.isArray(differences)) {
            throw new Error('Invalid diff result');
          }
                   
          console.log('Diff computation successful:', {
            diffCount: differences.length,
            sampleDiffs: differences.slice(0, 3)
          });

          // Apply diff results back to structure
          const diffResult = applyDiffToStructure(
            baseElement,
            baseTextMap,
            differences
          );

          diffResults[comparison.articleId] = [diffResult];
          console.log('Successfully processed comparison:', comparison.articleId);
          
        } catch (error) {
          console.error(`Failed to process comparison ${comparison.articleId}:`, error);
        }
      }
    } catch (error) {
      console.error('Error in loadAllContent:', error);
    } finally {
      isLoading = false;
    }
  }

  async function fetchLegislationContent(url: string): Promise<string> {
    console.log('Fetching legislation from:', url);
    
    try {
      const response = await fetch(`/api/legislation?url=${encodeURIComponent(url)}`);
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch legislation: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Received content length:', data.content?.length);
      return data.content || '';
    } catch (error) {
      console.error('Error fetching legislation:', error);
      throw error;
    }
  }

  $: if (comparisons?.length > 0 && selectedArticle?.url) {
    console.log('Triggering content load with:', {
      selectedArticle: selectedArticle?.url,
      comparisonsCount: comparisons.length
    });
    loadAllContent();
  }
</script>

<svelte:head>
  <link rel="stylesheet" href="/styles/diff-styles.css">
  <link rel="stylesheet" href="/styles/secondarylegislation.css">
</svelte:head>

<div class="comparison-container p-4">
  {#if isLoading}
    <div class="loading">Loading comparison data...</div>
  {:else if !baseContent}
    <div class="error">Failed to load base content</div>
  {:else}
    <div class="space-y-6">
      {#each comparisons as comparison (comparison.articleId)}
        <section class="diff-section bg-white shadow-sm rounded-lg p-4">
          <h2 class="text-lg font-semibold mb-4">
            {comparison.orderName} - {comparison.articleTitle}
          </h2>
          
          <div class="diff-content">
            {#if diffResults[comparison.articleId]}
              {#each diffResults[comparison.articleId] as diffResult}
                {@html diffResult.outerHTML}
              {/each}
            {:else}
              <div class="error">No comparison data available</div>
            {/if}
          </div>
        </section>
      {/each}
    </div>
  {/if}
</div>

<style>
  /* Add !important to ensure our styles take precedence */
  :global(.diff-content-wrapper) {
    display: inline !important;
  }
  
  :global(.diff-content .content.addition) {
    background-color: #e6ffe6 !important;
    text-decoration: underline !important;
    color: #006400 !important;
    display: inline !important;
    padding: 0.1em 0 !important;
  }
  
  :global(.diff-content .content.deletion) {
    background-color: #ffe6e6 !important;
    text-decoration: line-through !important;
    color: #640000 !important;
    display: inline !important;
    padding: 0.1em 0 !important;
  }
</style>
