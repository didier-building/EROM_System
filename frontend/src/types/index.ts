/**
 * TypeScript types for EROM system
 */

// User & Auth Types
export interface User {
  id: number;
  username: string;
  full_name: string;
  role: 'owner' | 'cashier';
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  data: {
    token: string;
    user: User;
  };
}

// Product & Inventory Types
export interface Category {
  id: number;
  name: string;
  description?: string;
}

export interface Brand {
  id: number;
  name: string;
  description?: string;
}

export interface Model {
  id: number;
  brand: number;
  brand_name?: string;
  name: string;
  release_year?: number;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  category: number;
  category_name?: string;
  brand: number;
  brand_name?: string;
  phone_model?: number;
  phone_model_name?: string;
  cost_price: string;
  selling_price: string;
  quantity_in_stock: number;
  quantity_in_field: number;
  total_quantity: number;
  reorder_level: number;
  is_low_stock: boolean;
  stock_value: string;
  is_active: boolean;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface ProductFormData {
  sku: string;
  name: string;
  category: number;
  brand: number;
  phone_model?: number;
  cost_price: number | string;
  selling_price: number | string;
  quantity_in_stock: number;
  reorder_level: number;
  description?: string;
  is_active: boolean;
}

export interface InventoryMovement {
  id: number;
  product: number;
  product_name?: string;
  movement_type: 'purchase' | 'sale' | 'transfer_to_agent' | 'return_from_agent' | 'adjustment' | 'reversal';
  quantity_delta: number;
  from_location: string;
  to_location: string;
  reference_id?: string;
  performed_by: number;
  performed_by_name?: string;
  notes?: string;
  created_at: string;
}

// Agent Types
export interface Agent {
  id: number;
  full_name: string;
  phone_number: string;
  id_number?: string;
  address?: string;
  area?: string;
  business_name?: string;
  credit_limit: string;
  total_debt: string;
  can_take_more_stock: boolean;
  is_active: boolean;
  is_trusted: boolean;
  created_at: string;
  notes?: string;
}

export interface AgentLedger {
  id: number;
  agent: number;
  agent_name?: string;
  product: number;
  product_name?: string;
  quantity: number;
  unit_price: string;
  debt_amount: string;
  transfer_date: string;
  is_paid: boolean;
  paid_amount: string;
  payment_date?: string;
  notes?: string;
}

export interface AgentPayment {
  id: number;
  agent: number;
  agent_name?: string;
  amount: string;
  payment_method: 'cash' | 'mobile_money' | 'bank_transfer';
  reference_number?: string;
  received_by: number;
  received_by_name?: string;
  created_at: string;
  notes?: string;
}

// Sales/Transaction Types
export interface Transaction {
  id: number;
  transaction_id: string;
  transaction_type: 'sale' | 'purchase' | 'return' | 'reversal';
  transaction_date: string;
  subtotal: string;
  tax_amount: string;
  discount_amount: string;
  total_amount: string;
  payment_method: 'cash' | 'mobile_money' | 'bank_transfer' | 'credit';
  amount_paid: string;
  change_given: string;
  customer_name?: string;
  customer_phone?: string;
  processed_by: number;
  processed_by_name?: string;
  items?: TransactionItem[];
  created_at: string;
}

export interface TransactionItem {
  id: number;
  transaction: number;
  product: number;
  product_name?: string;
  quantity: number;
  unit_price: string;
  discount: string;
  line_total: string;
}

export interface TransactionFormData {
  payment_method: 'cash' | 'mobile_money' | 'bank_transfer' | 'credit';
  amount_paid: number | string;
  customer_name?: string;
  customer_phone?: string;
  notes?: string;
  items: {
    product_id: number;
    quantity: number;
    unit_price: number | string;
    discount?: number | string;
  }[];
}

// Reconciliation Types
export interface Reconciliation {
  id: number;
  reconciliation_date: string;
  reconciliation_type: 'daily' | 'weekly' | 'monthly' | 'spot_check';
  status: 'in_progress' | 'completed' | 'approved' | 'rejected';
  performed_by: number;
  performed_by_name?: string;
  approved_by?: number;
  approved_by_name?: string;
  total_discrepancies: number;
  items?: ReconciliationItem[];
  notes?: string;
  created_at: string;
}

export interface ReconciliationItem {
  id: number;
  reconciliation: number;
  product: number;
  product_name?: string;
  system_count: number;
  physical_count: number;
  variance: number;
  has_discrepancy: boolean;
  discrepancy_reason?: string;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data: T;
  count?: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Dashboard Types
export interface DashboardStats {
  total_products: number;
  low_stock_products: number;
  total_agents: number;
  total_debt: string;
  today_sales: string;
  today_transactions: number;
  inventory_value: string;
}

// Filter/Search Types
export interface ProductFilters {
  search?: string;
  category?: number;
  brand?: number;
  is_low_stock?: boolean;
  is_active?: boolean;
}

export interface TransactionFilters {
  start_date?: string;
  end_date?: string;
  transaction_type?: string;
  payment_method?: string;
}
