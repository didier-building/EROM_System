/**
 * AddProductDialog - Dialog for adding new products
 */
import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Box,
  Alert,
} from '@mui/material';
import { inventoryApi } from '../../api';

interface Category {
  id: number;
  name: string;
}

interface Brand {
  id: number;
  name: string;
}

interface AddProductDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AddProductDialog({ open, onClose, onSuccess }: AddProductDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    category: '',
    brand: '',
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

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [field]: e.target.value });
  };

  const handleSubmit = async () => {
    setError(null);
    
    // Validation
    if (!formData.sku || !formData.name || !formData.category || !formData.brand || 
        !formData.cost_price || !formData.selling_price || !formData.quantity_in_stock) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      await inventoryApi.createProduct({
        sku: formData.sku,
        name: formData.name,
        category: parseInt(formData.category),
        brand: parseInt(formData.brand),
        cost_price: parseFloat(formData.cost_price),
        selling_price: parseFloat(formData.selling_price),
        quantity_in_stock: parseInt(formData.quantity_in_stock),
        reorder_level: parseInt(formData.reorder_level || '0'),
        description: formData.description,
        is_active: true,
      });
      
      // Reset form
      setFormData({
        sku: '',
        name: '',
        category: '',
        brand: '',
        cost_price: '',
        selling_price: '',
        quantity_in_stock: '',
        reorder_level: '',
        description: '',
      });
      
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create product');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Add New Product</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="SKU"
                value={formData.sku}
                onChange={handleChange('sku')}
                required
              />
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Product Name"
                value={formData.name}
                onChange={handleChange('name')}
                required
              />
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                select
                fullWidth
                label="Category"
                value={formData.category}
                onChange={handleChange('category')}
                required
              >
                <MenuItem value="">Select Category</MenuItem>
                {categories.map((cat) => (
                  <MenuItem key={cat.id} value={cat.id}>
                    {cat.name}
                  </MenuItem>
                ))}
              </TextField>
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                select
                fullWidth
                label="Brand"
                value={formData.brand}
                onChange={handleChange('brand')}
                required
              >
                <MenuItem value="">Select Brand</MenuItem>
                {brands.map((brand) => (
                  <MenuItem key={brand.id} value={brand.id}>
                    {brand.name}
                  </MenuItem>
                ))}
              </TextField>
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Cost Price (RWF)"
                type="number"
                value={formData.cost_price}
                onChange={handleChange('cost_price')}
                required
              />
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Selling Price (RWF)"
                type="number"
                value={formData.selling_price}
                onChange={handleChange('selling_price')}
                required
              />
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Quantity in Stock"
                type="number"
                value={formData.quantity_in_stock}
                onChange={handleChange('quantity_in_stock')}
                required
              />
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Reorder Level"
                type="number"
                value={formData.reorder_level}
                onChange={handleChange('reorder_level')}
              />
            </Box>
          </Box>
          <Box>
            <TextField
              fullWidth
              label="Description"
              multiline
              rows={3}
              value={formData.description}
              onChange={handleChange('description')}
            />
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} variant="contained" disabled={loading}>
          {loading ? 'Adding...' : 'Add Product'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
