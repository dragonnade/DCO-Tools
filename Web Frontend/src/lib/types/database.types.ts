// types/database.types.ts
export type Project = {
    id: string;
    project_number: string;
    project_name: string;
    project_url: string;
    created_at: string;
    updated_at: string;
    last_checked_at: string | null;
  }
  
  export type DocumentStage = {
    id: string;
    name: string;
    display_order: number;
    created_at: string;
  }
  
  export type DocumentCategory = {
    id: string;
    stage_id: string;
    name: string;
    created_at: string;
  }
  
  export type Document = {
    id: string;
    project_id: string;
    stage_id: string;
    category_id: string;
    title: string;
    description: string | null;
    file_size: string | null;
    file_type: string | null;
    published_date: string;
    uploaded_by: string | null;
    document_reference: string | null;
    url: string;
    examination_library_ref: string | null;
    created_at: string;
    updated_at: string;
    last_checked_at: string | null;
    is_available: boolean;
    metadata: Record<string, any> | null;
  }