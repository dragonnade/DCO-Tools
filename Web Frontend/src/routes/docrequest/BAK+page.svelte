<!-- src/routes/MqttControl.svelte -->
<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    // import { mqttService, type ConnectionStatus, type MqttMessage } from '$lib/mqttClient';
    // import { client } from '$lib/mqttClient';

    // const MQTT_Topic = "pi/commands";
    
    console.log("attempting to connect")

    // client.on("connect", () => {
    // client.subscribe("pi/commands", (err) => {
    //     if (!err) {
    //       client.publish("pi/commands", "Hello mqtt");
    //     }
    //   });
    // });

    // const sendCommand = client.publish(
    //     MQTT_TOPIC, "This is a message"
    // )

    // // Constants
    // const MQTT_TOPIC = 'pi/commands';

    // // Reactive variables
    // let connectionStatus: ConnectionStatus;
    // let lastMessage: MqttMessage | null;
    // let error: string | null;

    // // Subscribe to the MQTT stores
    // mqttService.connectionStatus.subscribe(status => connectionStatus = status);
    // mqttService.lastMessage.subscribe(message => lastMessage = message);
    // mqttService.error.subscribe(err => error = err);

    // // Send command to Raspberry Pi
    // const sendCommand = async () => {
    //     try {
    //         const message = {
    //             action: 'acknowledge',
    //             timestamp: new Date().toISOString()
    //         };

    //         await mqttService.publish(MQTT_TOPIC, message);
    //     } catch (err) {
    //         console.error('Error sending message:', err);
    //     }
    // };

    // onMount(() => {
    //     // Connect to MQTT broker when component mounts
    //     client.connect();
    // });

    onDestroy(() => {
        // Clean up MQTT connection when component is destroyed
        client.end();
    });
</script>

<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold mb-4">MQTT Control Panel</h1>
    
    <!-- Connection Status
    <div class="mb-4">
        <p class="text-sm">
            Trying something...
        </p>
        
        {#if error}
            <p class="text-sm text-red-600 mt-2">{error}</p>
        {/if}
    </div> -->
    <!-- Control Button -->
    <button
        on:click={null}
        class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
    >
        Connect...
    </button>
    <!-- Control Button -->
    <button
        on:click={null}
        class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
    >
        Send Command
    </button>

    <!-- Last Message Display -->
    <!-- {#if lastMessage} -->
        <div class="mt-4 p-4 bg-gray-100 rounded">
            <p class="text-sm">Nothing to see here.</p>

        </div>
    <!-- {/if} -->
</div>