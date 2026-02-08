/**
 * Inventory API service
 */
import { apiClient } from './client';
import type {
  Product,
  ProductFormData,
  Category,
  Brand,
  Model,
  InventoryMovement,
  ApiResponse,
  PaginatedResponse,
  ProductFilters,
} from '../types';

export const inventoryApi = {
  // Products
  getProducts: async (filters?: ProductFilters): Promise<PaginatedResponse<Product>> => {
    const response = await apiClient.get<PaginatedResponse<Product>>('/inventory/products/', {
      params: filters,
    });
    return response.data;
  },

  getProduct: async (id: number): Promise<Product> => {
    const response = await apiClient.get<Product>(`/inventory/products/${id}/`);
    return response.data;
  },

  createProduct: async (data: ProductFormData): Promise<Product> => {
    const response = await apiClient.post<Product>('/inventory/products/', data);
    return response.data;
  },

  updateProduct: async (id: number, data: Partial<ProductFormData>): Promise<Product> => {
    const response = await apiClient.patch<Product>(`/inventory/products/${id}/`, data);
    return response.data;
  },

  deleteProduct: async (id: number): Promise<void> => {
    await apiClient.delete(`/inventory/products/${id}/`);
  },

  // Low stock products
  getLowStockProducts: async (): Promise<ApiResponse<Product[]>> => {
    const response = await apiClient.get<ApiResponse<Product[]>>('/inventory/products/low_stock/');
    return response.data;
  },

  // Stock adjustment
  adjustStock: async (
    productId: number,
    data: { product_id: number; quantity_delta: number; reason: string }
  ): Promise<ApiResponse<{ new_quantity: number; movement_id: number }>> => {
    const response = await apiClient.post<ApiResponse<{ new_quantity: number; movement_id: number }>>(
      `/inventory/products/${productId}/adjust_stock/`,
      data
    );
    return response.data;
  },

  // Categories
  getCategories: async (): Promise<PaginatedResponse<Category>> => {
    const response = await apiClient.get<PaginatedResponse<Category>>('/inventory/categories/');
    return response.data;
  },

  createCategory: async (data: { name: string; description?: string }): Promise<Category> => {
    const response = await apiClient.post<Category>('/inventory/categories/', data);
    return response.data;
  },

  // Brands
  getBrands: async (): Promise<PaginatedResponse<Brand>> => {
    const response = await apiClient.get<PaginatedResponse<Brand>>('/inventory/brands/');
    return response.data;
  },

  createBrand: async (data: { name: string; description?: string }): Promise<Brand> => {
    const response = await apiClient.post<Brand>('/inventory/brands/', data);
    return response.data;
  },

  // Models
  getModels: async (brandId?: number): Promise<PaginatedResponse<Model>> => {
    const response = await apiClient.get<PaginatedResponse<Model>>('/inventory/models/', {
      params: { brand: brandId },
    });
    return response.data;
  },

  createModel: async (data: {
    brand: number;
    name: string;
    release_year?: number;
  }): Promise<Model> => {
    const response = await apiClient.post<Model>('/inventory/models/', data);
    return response.data;
  },

  // Inventory movements
  getMovements: async (productId?: number): Promise<PaginatedResponse<InventoryMovement>> => {
    const response = await apiClient.get<PaginatedResponse<InventoryMovement>>(
      '/inventory/movements/',
      {
        params: { product: productId },
      }
    );
    return response.data;
  },
};
