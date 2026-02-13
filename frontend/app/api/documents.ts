// Document API functions
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";
import { Document } from "@/types/document";

export const documentApi = {
  getDocuments: async (): Promise<Document[]> => {
    return apiCall<Document[]>(API_ENDPOINTS.DOCUMENTS, {
      method: "GET",
    });
  },

  getDocument: async (id: string): Promise<Document> => {
    return apiCall<Document>(API_ENDPOINTS.DOCUMENT(id), {
      method: "GET",
    });
  },

  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append("file", file);

    return apiCall<Document>(API_ENDPOINTS.DOCUMENTS, {
      method: "POST",
      body: formData,
    });
  },

  deleteDocument: async (id: string): Promise<void> => {
    await apiCall(API_ENDPOINTS.DOCUMENT(id), {
      method: "DELETE",
    });
  },
};
