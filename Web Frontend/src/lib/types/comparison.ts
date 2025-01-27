export interface ComparisonSelection {
    articleId: string;
    orderName: string;
    articleTitle: string;
    orderOfSelection: number;
    content?: string;
  }
  
  export interface DiffResult {
    text: string;
    type: 'addition' | 'deletion' | 'move' | 'unchanged';
    moved?: {
      from: number;
      to: number;
    };
  }