<!-- To Do:
1. Remove the MQTT elements, other than the input bar.
2. Make the table take up only part of the page.
3. Rename columns - Date/Time of request; Project; Status
4. Rename button to "Request project documents"
5. Add instructions - type project reference and hit button to update page with new documents. Refresh page to see status of request.
6. Profit!
-->

<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { writable } from 'svelte/store';
    // import { mqttService, connectionStatus, messages } from '$lib/mqttClient';
    import { supabase } from '$lib/supabaseClient';
    
    // Define proper types
    interface Command {
        created_at: string;
        project_number: string;
        status: string;
        error_message?: string;
    }

    let messageInput = '';
    // Replace $state with regular Svelte reactivity
    let commands: Command[] = [];
    let isLoading = false;

    onMount(() => {
        loadCommands();
    });


    async function loadCommands() {
        try {
            console.log('Connecting to Supabase')
            const { data, error } = await supabase
                .from('pi_commands')
                .select('*')
                .order('created_at', { ascending: false });
                // console.log("Success - if it's not showing, that's you're own affair")
            if (error) throw error;
            commands = data;
        } catch (error) {
            console.error('Error loading commands:', error);
        }
    }

    async function handleButtonClick() {
        if (!messageInput.trim().toUpperCase()) {
            return;
        }
        isLoading = true;
        try {
            const { error } = await supabase
                .from('pi_commands')
                .insert([
                    { project_number: messageInput.trim().toUpperCase() }
                ]);
                messageInput = ''
            if (error) throw error;
            
        } catch (error) {
            console.error('Error sending command:', error);
        } finally {
            isLoading = false;
        }
    }

    function getStatusClass(status: string): string {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800';
            case 'error':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-yellow-100 text-yellow-800';
        }
    }
</script>
<div class="page-container">
    <!-- Supabase Control Section -->
    <div class="content-card border rounded-lg p-4 bg-white shadow">
        <h2 class="text-xl font-bold mb-4">PINS Document Update Request</h2>
        <div class="message-input">
            <input 
                type="text" 
                bind:value={messageInput} 
                placeholder="Enter Project Reference"
            />
            <button
                on:click={handleButtonClick}
                class="primary-button"
            >
            <!-- Old button class settings: mb-6 px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-400 -->
                {isLoading ? 'Sending...' : 'Update project documents'}
            </button>
        </div>
    <!-- </div> -->
        <div class="border rounded-lg p-3 text-gray-800">
            <div class="overflow-x-auto">
                <p>Instructions: The system updates with new project documents daily. If new documents for a project are missing, simply submit the project number above. Refresh the page to see the status of your request.<b><b></p>
                <h3 class="font-bold">Last requested projects:</h3>
                <table class="w-full border-collapse border">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-4 py-2 text-left">Time of Request</th>
                            <th class="px-4 py-2 text-left">Project Requested</th>
                            <th class="px-4 py-2 text-left">Status</th>
                            <!-- <th class="px-4 py-2 text-left">Error</th> -->
                        </tr>
                    </thead>
                    <tbody>
                        {#each commands as cmd}
                            <tr class="border-t">
                                <td class="border-gray-300 px-4 py-2">
                                    {new Date(cmd.created_at).toLocaleString()}
                                </td>
                                <td class="border-gray-300 px-4 py-2">{cmd.project_number}</td>
                                <td class="border-gray-300 px-4 py-2">
                                    <span class="px-2 py-1 rounded text-sm {getStatusClass(cmd.status)}">
                                        {cmd.status}
                                    </span>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<style>
    .mqtt-container {
    padding: 1rem;
    }

    .message-input {
    margin: 1rem 0;
    }

    .messages {
    max-height: 300px;
    overflow-y: auto;
    }

    .message {
    margin: 0.5rem 0;
    }
</style>