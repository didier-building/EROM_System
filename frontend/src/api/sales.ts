/**
 * Sales/POS API service
 */
import { apiClient } from './client';
import type {
  Transaction,
  TransactionFormData,
  Reconciliation,
  ReconciliationItem,
  PaginatedResponse,
  ApiResponse,
  TransactionFilters,
  DashboardStats,
} from '../types';

export const salesApi = {
  // Transactions
  getTransactions: async (filters?: TransactionFilters): Promise<PaginatedResponse<Transaction>> => {
    const response = await apiClient.get<PaginatedResponse<Transaction>>('/sales/transactions/', {
      params: filters,
    });
    return response.data;
  },

  getTransaction: async (id: number): Promise<Transaction> => {
    const response = await apiClient.get<Transaction>(`/sales/transactions/${id}/`);
    return response.data;
  },

  createTransaction: async (data: TransactionFormData): Promise<ApiResponse<Transaction>> => {
    const response = await apiClient.post<ApiResponse<Transaction>>('/sales/transactions/create_sale/', data);
    return response.data;
  },

  // Today's sales
  getTodaySales: async (): Promise<ApiResponse<{
    total_sales: string;
    transaction_count: number;
    transactions: Transaction[];
  }>> => {
    const response = await apiClient.get<ApiResponse<any>>('/sales/transactions/today/');
    return response.data;
  },

  // Reconciliations
  getReconciliations: async (): Promise<PaginatedResponse<Reconciliation>> => {
    const response = await apiClient.get<PaginatedResponse<Reconciliation>>('/sales/reconciliations/');
    return response.data;
  },

  getReconciliation: async (id: number): Promise<Reconciliation> => {
    const response = await apiClient.get<Reconciliation>(`/sales/reconciliations/${id}/`);
    return response.data;
  },

  createReconciliation: async (data: {
    reconciliation_type: 'daily' | 'weekly' | 'monthly' | 'spot_check';
    notes?: string;
  }): Promise<ApiResponse<Reconciliation>> => {
    const response = await apiClient.post<ApiResponse<Reconciliation>>('/sales/reconciliations/', data);
    return response.data;
  },

  addReconciliationItem: async (reconciliationId: number, data: {
    product: number;
    system_count: number;
    physical_count: number;
    discrepancy_reason?: string;
  }): Promise<ApiResponse<ReconciliationItem>> => {
    const response = await apiClient.post<ApiResponse<ReconciliationItem>>(
      `/sales/reconciliations/${reconciliationId}/add_item/`,
      data
    );
    return response.data;
  },

  approveReconciliation: async (reconciliationId: number): Promise<ApiResponse<Reconciliation>> => {
    const response = await apiClient.post<ApiResponse<Reconciliation>>(
      `/sales/reconciliations/${reconciliationId}/approve/`
    );
    return response.data;
  },

  // Dashboard stats
  getDashboardStats: async (): Promise<ApiResponse<DashboardStats>> => {
    const response = await apiClient.get<ApiResponse<DashboardStats>>('/sales/transactions/dashboard_stats/');
    return response.data;
  },
};
