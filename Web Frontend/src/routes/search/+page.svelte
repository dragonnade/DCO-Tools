<script lang="ts">
    import { onMount } from 'svelte';
    import { runSearchTests } from './tests';

    onMount(async () => {
        await runSearchTests();
        // Only run tests in development
        // if (import.meta.env.DEV) {
            // await runSearchTests();
        // }
    });
</script>

<div class="p-4">
    <h1>Search Tests</h1>
    <p>Check the browser console for test results</p>
</div>
