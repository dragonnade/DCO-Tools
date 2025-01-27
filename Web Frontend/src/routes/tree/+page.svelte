<!-- ArticleNetwork.svelte -->
<script>
  import { onMount, untrack } from 'svelte';
  import * as d3 from 'd3';
  
  // Props for the component
  // export let selectedArticleId = null;
  let { selectedArticleId = 5 } = $props()

  // State management using Svelte 5's new reactive syntax
  let currentSimulation = $state(null);
  let graph = $state(null);
  let svg = $state(null);
  let simulation = $state(null);
  
  // Mock data - replace with your actual database data
  const mockData = {
    orders: [
      { id: 1, name: "The Network Rail (Ipswich Chord) Order 2012" },
      { id: 2, name: "The Network Rail (North Doncaster Chord) Order 2012" },
      { id: 4, name: "The Brechfa Forest West Wind Farm Order 2013" },
      { id: 5, name: "The Hinkley Point C (Nuclear Generating Station) Order 2013" },
      { id: 13, name: "The Network Rail (Redditch Branch Enhancement) Order 2013" },
      { id: 15, name: "The Network Rail (Norton Bridge Area Improvements) Order 2014" },
      { id: 23, name: "The Clocaenog Forest Wind Farm Order 2014" },
      { id: 30, name: "The Hornsea One Offshore Wind Farm Order 2014" },
      { id: 54, name: "The Hornsea Two Offshore Wind Farm Order 2016" }
    ],
    articles: [
      { id: 9, orderId: 1, title: "Article 9: Street works" },
      { id: 46, orderId: 2, title: "Article 11: Street works" },
      { id: 105, orderId: 4, title: "Article 10: Street works" },
      { id: 127, orderId: 5, title: "Article 13: Street works" },
      { id: 402, orderId: 13, title: "Article 8: Street works" },
      { id: 477, orderId: 15, title: "Article 9: Street works" },
      { id: 817, orderId: 23, title: "Article 10: Street works" },
      { id: 1055, orderId: 30, title: "Article 6: Street works" },
      { id: 1987, orderId: 54, title: "Article 9: Street works" }
    ],
    similarities: [
      { sourceArticleId: 105, targetArticleId: 46, similarity: 0.94 },
      { sourceArticleId: 402, targetArticleId: 46, similarity: 0.99 },
      { sourceArticleId: 402, targetArticleId: 105, similarity: 0.94 },
      { sourceArticleId: 477, targetArticleId: 9, similarity: 0.92 },
      { sourceArticleId: 817, targetArticleId: 105, similarity: 0.91 },
      { sourceArticleId: 1055, targetArticleId: 46, similarity: 0.97 },
      { sourceArticleId: 1055, targetArticleId: 105, similarity: 0.95 },
      { sourceArticleId: 1055, targetArticleId: 127, similarity: 0.91 },
      { sourceArticleId: 1987, targetArticleId: 46, similarity: 0.95 },
      { sourceArticleId: 1987, targetArticleId: 105, similarity: 0.93 }
    ]
  };

  // Function to process relationships and find the strongest paths
  function processRelationships(articleId) {
    console.log('Starting to process the relationships')
    const nodes = new Set();
    const links = new Set();
    const processed = new Set();
    
    // Add the selected article as the first node
    const selectedArticle = mockData.articles.find(a => a.id === articleId);
    const selectedOrder = mockData.orders.find(o => o.id === selectedArticle.orderId);
    nodes.add({
        id: articleId,
        title: selectedArticle.title,
        order: selectedOrder.name,
        similarity: 1  // This is the source node, so similarity is 1
    });

    // Helper function to find all paths to/from the selected article
    function findPaths(currentId, isAncestor, visited = new Set()) {
      console.log('Finding paths')
      if (visited.has(currentId)) return;
      visited.add(currentId);
      
      const similarities = mockData.similarities.filter(s => 
        isAncestor ? s.targetArticleId === currentId : s.sourceArticleId === currentId
      );
      
      for (const sim of similarities) {
        console.log('Processing an article')
        const relatedId = isAncestor ? sim.sourceArticleId : sim.targetArticleId;
        if (!processed.has(`${currentId}-${relatedId}`)) {
          const article = mockData.articles.find(a => a.id === relatedId);
          const order = mockData.orders.find(o => o.id === article.orderId);
          
          nodes.add({
            id: relatedId,
            title: article.title,
            order: order.name,
            similarity: sim.similarity
          });
          
          links.add({
            source: isAncestor ? relatedId : currentId,
            target: isAncestor ? currentId : relatedId,
            similarity: sim.similarity
          });
          
          processed.add(`${currentId}-${relatedId}`);
          findPaths(relatedId, isAncestor, visited);
        }
      }
    }
    
    // Find precedent articles (ancestors)
    findPaths(articleId, true);
    // Find influenced articles (descendants)
    findPaths(articleId, false);
    
    return {
      nodes: Array.from(nodes),
      links: Array.from(links)
    };
  }

  function updateVisualization() {
    if (!selectedArticleId || !svg) {
      console.log('Early return - missing selectedArticleId or svg');
      return;
    }
    
    // Clear existing visualization
    d3.select(svg).selectAll("*").remove();
    
    // Process the relationships
    console.log('Processing relationships');
    const processedGraph = untrack(() => processRelationships(selectedArticleId));
    graph = processedGraph;
    console.log('Processed graph:', graph);
    
    // Set up the SVG
    const width = 800;
    const height = 600;
    const svgElement = d3.select(svg)
      .attr("viewBox", [0, 0, width, height])
      .attr("width", "100%")
      .attr("height", "100%");

    // Clear existing visualization
    svgElement.selectAll("*").remove();
    
    // Create the force simulation
    console.log('Setting up simulation');
    simulation = d3.forceSimulation(graph.nodes)
      .force("link", d3.forceLink(graph.links)
        .id(d => d.id)
        .distance(d => 200 - d.similarity * 100))
      .force("charge", d3.forceManyBody().strength(-1000))
      .force("center", d3.forceCenter(width / 2, height / 2));
    
    // Create the links
    console.log('Creating links')
    const link = svgElement.append("g")
      .selectAll("line")
      .data(graph.links)
      .join("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", d => d.similarity)
      .attr("stroke-width", d => d.similarity * 5);
    
    // Create the nodes
    console.log('Creating nodes')
    const node = svgElement.append("g")
      .selectAll("g")
      .data(graph.nodes)
      .join("g");
    
    // Add circles for nodes
    console.log('Adding circles for nodes')
    node.append("circle")
      .attr("r", 30)
      .attr("fill", d => d.id === selectedArticleId ? "#4CAF50" : 
                        d.similarity > 0.8 ? "#2196F3" : "#FFC107");
    
    // Add text labels
    console.log('Adding text labels')
    node.append("text")
      .text(d => d.title)
      .attr("text-anchor", "middle")
      .attr("dy", -40)
      .attr("font-size", "12px")
      .attr("fill", "#333");
    
    // Add order labels
    node.append("text")
      .text(d => d.order)
      .attr("text-anchor", "middle")
      .attr("dy", 50)
      .attr("font-size", "10px")
      .attr("fill", "#666");
    
    // Add similarity labels on links
    svgElement.append("g")
      .selectAll("text")
      .data(graph.links)
      .join("text")
      .attr("text-anchor", "middle")
      .attr("dy", -5)
      .text(d => `${(d.similarity * 100).toFixed(1)}%`)
      .attr("font-size", "10px")
      .attr("fill", "#666");
    
    // Update positions on each tick
    simulation.on("tick", () => {
      console.log('Simulation tick');
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
      
      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });
  }

  $effect(() => {
  console.log('Effect running with selectedArticleId: ', selectedArticleId);
  // selectedArticleId
  if (!selectedArticleId || !svg) {
    console.log('Early return - missing selectedArticleId or svg');
    return;
  }

  untrack(() => {
    // Process the relationships first
    const processedGraph = processRelationships(selectedArticleId);
    graph = processedGraph;
    
    // Then handle the visualization
    updateVisualization(processedGraph);
    });
  });

  
  // Initialize the component
  onMount(() => {
    svg = document.querySelector("#network-svg");
  });
</script>

<div class="w-full max-w-4xl mx-auto p-4">
  <div class="mb-4">
    <select 
      bind:value={selectedArticleId}
      class="w-full p-2 border rounded">
      <option value={null}>Select an article...</option>
      {#each mockData.articles as article}
        <option value={article.id}>{article.title}</option>
      {/each}
    </select>
  </div>
  
  <div class="border rounded-lg p-4 bg-white shadow-sm">
    <svg id="network-svg" />
  </div>
</div>