// src/lib/types/search.ts
export interface SearchTerm {
  type: 'include' | 'exclude' | 'proximity';
  value: string | string[];  // single term or array for proximity
  proximityDistance?: number;
}

export interface FilterParams {
  stages?: string[];
  categories?: string[];
  applicationTypes?: string[];
  dateRange?: {
    start?: string;
    end?: string;
  };
}

export interface AdvancedSearchParams {
  searchTerms: SearchTerm[];
  filters?: FilterParams;
  page: number;
  pageSize: number;
}

export interface SearchResponse {
  documents: string[]; // Replace 'any' with your document type
  totalCount: number;
  currentPage: number;
  pageSize: number;
}