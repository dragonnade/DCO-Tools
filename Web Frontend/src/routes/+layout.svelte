<!-- src/routes/+layout.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    // import { initializeStaticCaches } from '$lib/services/cacheService';
    import Navbar from '$lib/components/Navbar.svelte';
    import '../app.css';

    // // Initialize caches when the app first loads
    // onMount(async () => {
    //     try {
    //         await initializeStaticCaches();
    //         console.log('Static caches initialized successfully');
    //     } catch (error) {
    //         console.error('Failed to initialize static caches:', error);
    //         // You might want to show a user-friendly error message here
    //     }
    // });
</script>
<title>DCO Tools</title>
<Navbar />
<main>
    <slot />
</main>