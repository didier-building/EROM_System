/**
 * InventoryPage - Product inventory management
 */
import { useEffect, useState, useMemo, useCallback, lazy, Suspense } from 'react';
import {
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { inventoryApi } from '../../api';
import type { Product } from '../../types';

const AddProductDialog = lazy(() => import('../../components/inventory/AddProductDialog'));
const EditProductDialog = lazy(() => import('../../components/inventory/EditProductDialog'));

export default function InventoryPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  const loadProducts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await inventoryApi.getProducts();
      setProducts(response.results);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load products');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  const handleEdit = useCallback((product: Product) => {
    setSelectedProduct(product);
    setOpenEditDialog(true);
  }, []);

  const handleDelete = useCallback(async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return;
    }

    try {
      await inventoryApi.deleteProduct(id);
      setProducts(products.filter((p) => p.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to delete product');
    }
  }, [products]);

  const filteredProducts = useMemo(() => {
    if (!searchQuery) return products;
    const query = searchQuery.toLowerCase();
    return products.filter(
      (product) =>
        product.name.toLowerCase().includes(query) ||
        (product.category_name && product.category_name.toLowerCase().includes(query)) ||
        (product.brand_name && product.brand_name.toLowerCase().includes(query))
    );
  }, [products, searchQuery]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <div>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Inventory Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your product inventory
          </Typography>
        </div>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />} 
          size="large"
          onClick={() => setOpenAddDialog(true)}
        >
          Add Product
        </Button>
      </Box>

      <AddProductDialog
        open={openAddDialog}
        onClose={() => setOpenAddDialog(false)}
        onSuccess={loadProducts}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search products by name, category, or brand..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Product</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Brand</TableCell>
              <TableCell align="right">Price (RWF)</TableCell>
              <TableCell align="right">Stock</TableCell>
              <TableCell align="right">Min Stock</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredProducts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary" sx={{ py: 4 }}>
                    {searchQuery ? 'No products found' : 'No products yet. Add your first product!'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredProducts.map((product) => (
                <TableRow key={product.id} hover>
                  <TableCell>
                    <Typography fontWeight="medium">{product.name}</Typography>
                  </TableCell>
                  <TableCell>{product.category_name}</TableCell>
                  <TableCell>{product.brand_name}</TableCell>
                  <TableCell align="right">{parseInt(product.selling_price).toLocaleString()}</TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                      {product.quantity_in_stock <= product.reorder_level && (
                        <WarningIcon color="warning" fontSize="small" />
                      )}
                      {product.quantity_in_stock}
                    </Box>
                  </TableCell>
                  <TableCell align="right">{product.reorder_level}</TableCell>
                  <TableCell>
                    {product.quantity_in_stock <= product.reorder_level ? (
                      <Chip label="Low Stock" color="warning" size="small" />
                    ) : product.quantity_in_stock === 0 ? (
                      <Chip label="Out of Stock" color="error" size="small" />
                    ) : (
                      <Chip label="In Stock" color="success" size="small" />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" color="primary" onClick={() => handleEdit(product)}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDelete(product.id)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Suspense fallback={null}>
        <AddProductDialog
          open={openAddDialog}
          onClose={() => setOpenAddDialog(false)}
          onSuccess={loadProducts}
        />

        <EditProductDialog
          open={openEditDialog}
          onClose={() => {
            setOpenEditDialog(false);
            setSelectedProduct(null);
          }}
          onSuccess={loadProducts}
          product={selectedProduct}
        />
      </Suspense>
    </Box>
  );
}
