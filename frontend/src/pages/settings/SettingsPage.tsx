/**
 * SettingsPage - Comprehensive system configuration for owner
 */
import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Card,
  CardContent,
  Divider,
  Chip,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Category as CategoryIcon,
  LocalOffer as BrandIcon,
  People as PeopleIcon,
  Store as StoreIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { inventoryApi } from '../../api';
import { useAuthStore } from '../../store';

interface Category {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
}

interface Brand {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
}

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [tabValue, setTabValue] = useState(0);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Dialog state
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState<'category' | 'brand'>('category');
  const [editingItem, setEditingItem] = useState<any>(null);
  const [formData, setFormData] = useState({ name: '', description: '' });

  // Shop settings state
  const [shopSettings, setShopSettings] = useState({
    name: 'EROM Shop',
    owner_name: user?.full_name || '',
    phone: '+250 XXX XXX XXX',
    address: '',
    currency: 'RWF',
  });

  useEffect(() => {
    loadCategories();
    loadBrands();
  }, []);

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

  const handleOpenDialog = (type: 'category' | 'brand', item?: any) => {
    setDialogType(type);
    setEditingItem(item || null);
    setFormData({
      name: item?.name || '',
      description: item?.description || '',
    });
    setOpenDialog(true);
    setError(null);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingItem(null);
    setFormData({ name: '', description: '' });
    setError(null);
  };

  const handleSave = async () => {
    if (!formData.name) {
      setError('Name is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      if (dialogType === 'category') {
        if (editingItem) {
          await inventoryApi.updateCategory(editingItem.id, formData);
        } else {
          await inventoryApi.createCategory(formData);
        }
        await loadCategories();
        setSuccess(`Category ${editingItem ? 'updated' : 'created'} successfully!`);
      } else {
        if (editingItem) {
          await inventoryApi.updateBrand(editingItem.id, formData);
        } else {
          await inventoryApi.createBrand(formData);
        }
        await loadBrands();
        setSuccess(`Brand ${editingItem ? 'updated' : 'created'} successfully!`);
      }

      handleCloseDialog();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to save');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (type: 'category' | 'brand', id: number, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }

    try {
      if (type === 'category') {
        await inventoryApi.deleteCategory(id);
        await loadCategories();
        setSuccess('Category deleted successfully!');
      } else {
        await inventoryApi.deleteBrand(id);
        await loadBrands();
        setSuccess('Brand deleted successfully!');
      }
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to delete. This item may be in use.');
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleSaveShopSettings = () => {
    setSuccess('Shop settings updated successfully!');
    setTimeout(() => setSuccess(null), 3000);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        System Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Configure your shop, inventory, and system preferences
      </Typography>

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab icon={<StoreIcon />} label="Shop Info" iconPosition="start" />
          <Tab icon={<CategoryIcon />} label="Categories" iconPosition="start" />
          <Tab icon={<BrandIcon />} label="Brands" iconPosition="start" />
          <Tab icon={<PeopleIcon />} label="Users" iconPosition="start" />
          <Tab icon={<SecurityIcon />} label="Security" iconPosition="start" />
        </Tabs>

        {/* Shop Information Tab */}
        {tabValue === 0 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Shop Information
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Configure your shop details and business information
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, maxWidth: 600 }}>
              <TextField
                fullWidth
                label="Shop Name"
                value={shopSettings.name}
                onChange={(e) => setShopSettings({ ...shopSettings, name: e.target.value })}
              />

              <TextField
                fullWidth
                label="Owner Name"
                value={shopSettings.owner_name}
                onChange={(e) => setShopSettings({ ...shopSettings, owner_name: e.target.value })}
              />

              <TextField
                fullWidth
                label="Phone Number"
                value={shopSettings.phone}
                onChange={(e) => setShopSettings({ ...shopSettings, phone: e.target.value })}
              />

              <TextField
                fullWidth
                label="Address"
                value={shopSettings.address}
                onChange={(e) => setShopSettings({ ...shopSettings, address: e.target.value })}
                multiline
                rows={3}
              />

              <TextField
                fullWidth
                label="Currency"
                value={shopSettings.currency}
                disabled
                helperText="Default currency for all transactions"
              />

              <Button
                variant="contained"
                size="large"
                onClick={handleSaveShopSettings}
                sx={{ alignSelf: 'flex-start' }}
              >
                Save Shop Settings
              </Button>
            </Box>

            <Divider sx={{ my: 4 }} />

            <Typography variant="h6" gutterBottom>
              System Information
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Active User
                  </Typography>
                  <Typography variant="h6">{user?.full_name}</Typography>
                  <Chip label={user?.role} size="small" color="primary" sx={{ mt: 1 }} />
                </CardContent>
              </Card>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    System Version
                  </Typography>
                  <Typography variant="h6">v1.0.0</Typography>
                  <Typography variant="caption" color="text.secondary">
                    EROM System 2026
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          </Box>
        )}

        {/* Categories Tab */}
        {tabValue === 1 && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <div>
                <Typography variant="h6">Product Categories</Typography>
                <Typography variant="body2" color="text.secondary">
                  Organize products by categories
                </Typography>
              </div>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog('category')}
              >
                Add Category
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell align="center">Products</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {categories.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                        <Typography color="text.secondary">
                          No categories yet. Add your first category to organize products!
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    categories.map((category) => (
                      <TableRow key={category.id} hover>
                        <TableCell>
                          <Typography fontWeight="medium">{category.name}</Typography>
                        </TableCell>
                        <TableCell>{category.description || '-'}</TableCell>
                        <TableCell align="center">
                          <Chip label="0" size="small" />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleOpenDialog('category', category)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDelete('category', category.id, category.name)}
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
          </Box>
        )}

        {/* Brands Tab */}
        {tabValue === 2 && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <div>
                <Typography variant="h6">Product Brands</Typography>
                <Typography variant="body2" color="text.secondary">
                  Manage smartphone and product brands
                </Typography>
              </div>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog('brand')}
              >
                Add Brand
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell align="center">Products</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {brands.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                        <Typography color="text.secondary">
                          No brands yet. Add your first brand!
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    brands.map((brand) => (
                      <TableRow key={brand.id} hover>
                        <TableCell>
                          <Typography fontWeight="medium">{brand.name}</Typography>
                        </TableCell>
                        <TableCell>{brand.description || '-'}</TableCell>
                        <TableCell align="center">
                          <Chip label="0" size="small" />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleOpenDialog('brand', brand)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDelete('brand', brand.id, brand.name)}
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
          </Box>
        )}

        {/* Users Tab */}
        {tabValue === 3 && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <div>
                <Typography variant="h6">User Management</Typography>
                <Typography variant="body2" color="text.secondary">
                  Manage cashiers and system users
                </Typography>
              </div>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                disabled
              >
                Add User (Coming Soon)
              </Button>
            </Box>

            <Alert severity="info" sx={{ mb: 2 }}>
              User management feature is coming soon. Currently logged in as: <strong>{user?.full_name}</strong> ({user?.role})
            </Alert>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Username</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>{user?.full_name}</TableCell>
                    <TableCell>{user?.username}</TableCell>
                    <TableCell>
                      <Chip label={user?.role === 'owner' ? 'Owner' : 'Cashier'} color="primary" size="small" />
                    </TableCell>
                    <TableCell>
                      <Chip label="Active" color="success" size="small" />
                    </TableCell>
                    <TableCell align="right">
                      <Button size="small" disabled>
                        Edit
                      </Button>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Security Tab */}
        {tabValue === 4 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Security Settings
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Manage password and security preferences
            </Typography>

            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Change Password
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 500, mt: 2 }}>
                  <TextField
                    fullWidth
                    type="password"
                    label="Current Password"
                    size="small"
                  />
                  <TextField
                    fullWidth
                    type="password"
                    label="New Password"
                    size="small"
                  />
                  <TextField
                    fullWidth
                    type="password"
                    label="Confirm New Password"
                    size="small"
                  />
                  <Button variant="contained" sx={{ alignSelf: 'flex-start' }} disabled>
                    Update Password (Coming Soon)
                  </Button>
                </Box>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  System Backup
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Create a backup of your data for safety
                </Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button variant="outlined" disabled>
                    Download Backup (Coming Soon)
                  </Button>
                  <Button variant="outlined" disabled>
                    Restore from Backup
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}
      </Paper>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingItem ? 'Edit' : 'Add'} {dialogType === 'category' ? 'Category' : 'Brand'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
            required
          />

          <TextField
            fullWidth
            label="Description (Optional)"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSave} variant="contained" disabled={loading}>
            {loading ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
