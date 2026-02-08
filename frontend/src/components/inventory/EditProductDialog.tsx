/**
 * EditProductDialog - Dialog for editing existing products
 */
import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import { inventoryApi } from '../../api';
import type { Product, Category, Brand } from '../../types';

interface EditProductDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  product: Product | null;
}

export default function EditProductDialog({ open, onClose, onSuccess, product }: EditProductDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    category: '' as any,
    brand: '' as any,
    cost_price: '',
    selling_price: '',
    quantity_in_stock: '',
    reorder_level: '',
    description: '',
  });

  useEffect(() => {
    if (open) {
      loadCategories();
      loadBrands();
    }
  }, [open]);

  useEffect(() => {
    // Only set form data after categories and brands have loaded
    if (open && product && categories.length > 0 && brands.length > 0) {
      setFormData({
        sku: product.sku || '',
        name: product.name || '',
        category: product.category || '',
        brand: product.brand || '',
        cost_price: product.cost_price?.toString() || '0',
        selling_price: product.selling_price?.toString() || '0',
        quantity_in_stock: product.quantity_in_stock?.toString() || '0',
        reorder_level: product.reorder_level?.toString() || '0',
        description: product.description || '',
      });
    }
  }, [open, product, categories, brands]);

  const loadCategories = async () => {
    try {
      const response = await inventoryApi.getCategories();
      setCategories(response.results);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadBrands = async () => {
    try {
      const response = await inventoryApi.getBrands();
      setBrands(response.results);
    } catch (err) {
      console.error('Failed to load brands:', err);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!product) return;
    
    setError(null);

    // Validation
    if (!formData.sku || !formData.name || !formData.category || !formData.brand ||
        !formData.selling_price || !formData.quantity_in_stock) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      await inventoryApi.updateProduct(product.id, {
        sku: formData.sku,
        name: formData.name,
        category: formData.category,
        brand: formData.brand,
        cost_price: parseFloat(formData.cost_price) || 0,
        selling_price: parseFloat(formData.selling_price),
        quantity_in_stock: parseInt(formData.quantity_in_stock),
        reorder_level: parseInt(formData.reorder_level) || 0,
        description: formData.description,
      });
      
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update product');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>Edit Product</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mt: 1 }}>
            <TextField
              fullWidth
              label="SKU"
              name="sku"
              value={formData.sku}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <TextField
              fullWidth
              label="Product Name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <TextField
              fullWidth
              select
              label="Category"
              name="category"
              value={formData.category}
              onChange={handleChange}
              required
              disabled={loading}
            >
              {categories.map((cat) => (
                <MenuItem key={cat.id} value={cat.id}>
                  {cat.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              fullWidth
              select
              label="Brand"
              name="brand"
              value={formData.brand}
              onChange={handleChange}
              required
              disabled={loading}
            >
              {brands.map((brand) => (
                <MenuItem key={brand.id} value={brand.id}>
                  {brand.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              fullWidth
              label="Cost Price"
              name="cost_price"
              type="number"
              value={formData.cost_price}
              onChange={handleChange}
              disabled={loading}
              inputProps={{ step: '0.01', min: '0' }}
            />
            <TextField
              fullWidth
              label="Selling Price"
              name="selling_price"
              type="number"
              value={formData.selling_price}
              onChange={handleChange}
              required
              disabled={loading}
              inputProps={{ step: '0.01', min: '0' }}
            />
            <TextField
              fullWidth
              label="Quantity in Stock"
              name="quantity_in_stock"
              type="number"
              value={formData.quantity_in_stock}
              onChange={handleChange}
              required
              disabled={loading}
              inputProps={{ min: '0' }}
            />
            <TextField
              fullWidth
              label="Reorder Level"
              name="reorder_level"
              type="number"
              value={formData.reorder_level}
              onChange={handleChange}
              disabled={loading}
              inputProps={{ min: '0' }}
            />
            <TextField
              fullWidth
              label="Description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              multiline
              rows={3}
              disabled={loading}
              sx={{ gridColumn: { sm: '1 / -1' } }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Updating...' : 'Update Product'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
