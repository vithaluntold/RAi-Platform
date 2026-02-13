// Common types
export interface ApiResponse<T> {
  data: T;
  status: string;
  message?: string;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

export interface PaginationParams {
  page: number;
  limit: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}
