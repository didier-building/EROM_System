/**
 * Agents API service
 */
import { apiClient } from './client';
import type { Agent, AgentLedger, AgentPayment, PaginatedResponse, ApiResponse } from '../types';

export const agentsApi = {
  // Agents
  getAgents: async (params?: { search?: string; is_active?: boolean }): Promise<PaginatedResponse<Agent>> => {
    const response = await apiClient.get<PaginatedResponse<Agent>>('/agents/agents/', { params });
    return response.data;
  },

  getAgent: async (id: number): Promise<Agent> => {
    const response = await apiClient.get<Agent>(`/agents/agents/${id}/`);
    return response.data;
  },

  createAgent: async (data: {
    full_name: string;
    phone_number: string;
    id_number?: string;
    address?: string;
    area?: string;
    business_name?: string;
    credit_limit: number | string;
    is_trusted?: boolean;
    notes?: string;
  }): Promise<Agent> => {
    const response = await apiClient.post<Agent>('/agents/agents/', data);
    return response.data;
  },

  updateAgent: async (id: number, data: Partial<Agent>): Promise<Agent> => {
    const response = await apiClient.patch<Agent>(`/agents/agents/${id}/`, data);
    return response.data;
  },

  // Agent ledger (stock transfers)
  getAgentLedger: async (agentId: number): Promise<AgentLedger[]> => {
    const response = await apiClient.get<{success: boolean; count: number; results: AgentLedger[]}>(`/agents/agents/${agentId}/ledger/`);
    return response.data.results;
  },

  transferStock: async (agentId: number, data: {
    product_id: number;
    quantity: number;
    unit_price: number | string;
    debt_amount: number;
    notes?: string;
  }): Promise<ApiResponse<AgentLedger>> => {
    const response = await apiClient.post<ApiResponse<AgentLedger>>(`/agents/agents/${agentId}/transfer_stock/`, data);
    return response.data;
  },

  // Agent payments
  getAgentPayments: async (agentId: number): Promise<PaginatedResponse<AgentPayment>> => {
    const response = await apiClient.get<PaginatedResponse<AgentPayment>>(`/agents/agents/${agentId}/payments/`);
    return response.data;
  },

  recordPayment: async (data: {
    agent: number;
    amount: number | string;
    payment_method: 'cash' | 'mobile_money' | 'bank_transfer';
    reference_number?: string;
    notes?: string;
  }): Promise<ApiResponse<AgentPayment>> => {
    const response = await apiClient.post<ApiResponse<AgentPayment>>('/agents/payments/', data);
    return response.data;
  },

  // Agent debt summary
  getDebtSummary: async (agentId: number): Promise<ApiResponse<{
    total_debt: string;
    debt_by_age: {
      '0-7': string;
      '8-30': string;
      '31-60': string;
      '61-90': string;
      '90+': string;
    };
  }>> => {
    const response = await apiClient.get<ApiResponse<any>>(`/agents/agents/${agentId}/debt_summary/`);
    return response.data;
  },
};
