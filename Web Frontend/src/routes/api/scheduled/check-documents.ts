// api/scheduled/check-documents.ts
import { DocumentUpdateService } from '../../services/documentUpdateService';

export async function handler(event: any, context: any) {
  try {
    // Check if this is a scheduled event
    if (event.source !== 'aws.events') {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Invalid event source' })
      };
    }

    await DocumentUpdateService.updateAllProjects();

    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Document check completed successfully' })
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Failed to check documents',
        details: error instanceof Error ? error.message : 'Unknown error'
      })
    };
  }
}