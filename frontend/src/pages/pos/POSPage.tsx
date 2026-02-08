/**
 * POSPage - Point of Sale transaction interface
 */
import { useState, useEffect, useMemo, useCallback, lazy, Suspense } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Card,
  CardContent,
  Divider,
  TextField,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
  Alert,
  InputAdornment,
  CircularProgress,
  Chip,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  Delete as DeleteIcon,
  ShoppingCart as CartIcon,
  Search as SearchIcon,
  SwapHoriz as TransferIcon,
} from '@mui/icons-material';
import { inventoryApi, salesApi } from '../../api';
import { useAuthStore } from '../../store';
import type { Product } from '../../types';

const StockTransferDialog = lazy(() => import('../../components/agents/StockTransferDialog'));

interface CartItem {
  id: number;
  sku: string;
  name: string;
  price: number;
  quantity: number;
  available: number;
}

export default function POSPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState(0); // 0 = Cash Sales, 1 = Agent Distribution
  const [products, setProducts] = useState<Product[]>([]);
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [transactionType, setTransactionType] = useState('CASH');
  const [openTransferDialog, setOpenTransferDialog] = useState(false);
  
  const isOwner = useMemo(() => user?.role === 'owner', [user?.role]);
  const [customerInfo, setCustomerInfo] = useState('');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadProducts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await inventoryApi.getProducts();
      setProducts(response.results);
      setFilteredProducts(response.results);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load products');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  useEffect(() => {
    if (searchQuery) {
      const filtered = products.filter(
        (p) =>
          p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.category_name?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredProducts(filtered);
    } else {
      setFilteredProducts(products);
    }
  }, [searchQuery, products]);

  const addToCart = (product: Product) => {
    const existing = cart.find((i) => i.id === product.id);
    if (existing) {
      if (existing.quantity < existing.available) {
        setCart(
          cart.map((i) =>
            i.id === product.id ? { ...i, quantity: i.quantity + 1 } : i
          )
        );
      } else {
        setError(`Only ${existing.available} units available in stock`);
        setTimeout(() => setError(null), 3000);
      }
    } else {
      setCart([
        ...cart,
        {
          id: product.id,
          sku: product.sku,
          name: product.name,
          price: product.selling_price,
          quantity: 1,
          available: product.quantity_in_stock,
        },
      ]);
    }
  };

  const updateQuantity = (id: number, delta: number) => {
    setCart(
      cart
        .map((item) => {
          if (item.id === id) {
            const newQuantity = item.quantity + delta;
            if (newQuantity > item.available) {
              setError(`Only ${item.available} units available`);
              setTimeout(() => setError(null), 3000);
              return item;
            }
            return { ...item, quantity: Math.max(0, newQuantity) };
          }
          return item;
        })
        .filter((item) => item.quantity > 0)
    );
  };

  const removeFromCart = (id: number) => {
    setCart(cart.filter((item) => item.id !== id));
  };

  const calculateTotal = () => {
    return cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  };

  const handleCheckout = async () => {
    if (cart.length === 0) {
      setError('Cart is empty');
      return;
    }

    try {
      setProcessing(true);
      setError(null);

      // Map frontend payment method to backend format
      const paymentMethodMap: Record<string, string> = {
        'CASH': 'cash',
        'MOMO': 'mobile_money',
        'CREDIT': 'credit',
        'BANK': 'bank_transfer',
      };

      const total = calculateTotal();

      await salesApi.createTransaction({
        items: cart.map((item) => ({
          product_id: item.id,
          quantity: item.quantity,
          unit_price: item.price,
          discount: 0,
        })),
        payment_method: paymentMethodMap[transactionType],
        amount_paid: total,
        customer_name: customerInfo || '',
        customer_phone: '',
        notes: '',
      });

      setSuccess('Transaction completed successfully!');
      setCart([]);
      setCustomerInfo('');
      setSearchQuery('');
      loadProducts(); // Refresh product stock
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to complete transaction');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <div>
          <Typography variant="h4" fontWeight="bold">
            Point of Sale
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage sales and field distribution
          </Typography>
        </div>
        <Button
          variant="contained"
          color="success"
          size="large"
          startIcon={<TransferIcon />}
          onClick={() => setOpenTransferDialog(true)}
        >
          Give to Agent
        </Button>
      </Box>

      {/* Tabs for Cash Sales vs Agent Distribution */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={activeTab} onChange={(_, val) => setActiveTab(val)}>
          <Tab icon={<CartIcon />} label="Cash Sales" iconPosition="start" />
          <Tab icon={<TransferIcon />} label="Agent Distribution" iconPosition="start" />
        </Tabs>
      </Paper>

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

      <Box sx={{ display: 'flex', gap: 3, flexWrap: { xs: 'wrap', md: 'nowrap' } }}>
        {/* Product Selection - Left Side */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 60%' } }}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <TextField
              fullWidth
              placeholder="Search products by name, SKU, or category..."
              size="small"
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

          <Paper sx={{ p: 2, maxHeight: 'calc(100vh - 300px)', overflowY: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Available Products ({filteredProducts.length})
            </Typography>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : filteredProducts.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                {searchQuery ? 'No products found' : 'No products available in stock'}
              </Typography>
            ) : (
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mt: 2 }}>
                {filteredProducts.map((product) => (
                  <Card
                    key={product.id}
                    sx={{
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      '&:hover': { boxShadow: 3, transform: 'translateY(-2px)' },
                    }}
                    onClick={() => addToCart(product)}
                  >
                    <CardContent>
                      <Typography variant="subtitle1" fontWeight="bold" noWrap>
                        {product.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        SKU: {product.sku}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        {product.category_name}
                      </Typography>
                      <Divider sx={{ my: 1 }} />
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="h6" color="primary" fontWeight="bold">
                          {product.selling_price.toLocaleString()} RWF
                        </Typography>
                        <Chip
                          label={`${product.quantity_in_stock} in stock`}
                          size="small"
                          color={product.quantity_in_stock <= product.reorder_level ? 'warning' : 'success'}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </Paper>
        </Box>

        {/* Cart - Right Side */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 40%' } }}>
          <Card sx={{ position: { md: 'sticky' }, top: { md: 16 } }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <CartIcon />
                <Typography variant="h6">Shopping Cart ({cart.length})</Typography>
              </Box>

              {cart.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                  Cart is empty. Click on products to add them.
                </Typography>
              ) : (
                <>
                  <Box sx={{ maxHeight: '300px', overflowY: 'auto', mb: 2 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Product</TableCell>
                          <TableCell align="right">Qty</TableCell>
                          <TableCell align="right">Total</TableCell>
                          <TableCell />
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {cart.map((item) => (
                          <TableRow key={item.id}>
                            <TableCell>
                              <Typography variant="body2" fontWeight="bold">
                                {item.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {item.price.toLocaleString()} RWF each
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, justifyContent: 'flex-end' }}>
                                <IconButton
                                  size="small"
                                  onClick={() => updateQuantity(item.id, -1)}
                                >
                                  <RemoveIcon fontSize="small" />
                                </IconButton>
                                <Typography variant="body2" sx={{ minWidth: 20, textAlign: 'center' }}>
                                  {item.quantity}
                                </Typography>
                                <IconButton
                                  size="small"
                                  onClick={() => updateQuantity(item.id, 1)}
                                >
                                  <AddIcon fontSize="small" />
                                </IconButton>
                              </Box>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2" fontWeight="bold">
                                {(item.price * item.quantity).toLocaleString()}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => removeFromCart(item.id)}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="h5" align="right" fontWeight="bold" color="primary">
                      Total: {calculateTotal().toLocaleString()} RWF
                    </Typography>
                  </Box>

                  <TextField
                    select
                    fullWidth
                    label="Payment Method"
                    value={transactionType}
                    onChange={(e) => setTransactionType(e.target.value)}
                    sx={{ mb: 2 }}
                    size="small"
                  >
                    <MenuItem value="CASH">Cash</MenuItem>
                    <MenuItem value="MOMO">Mobile Money</MenuItem>
                    <MenuItem value="CREDIT">Credit</MenuItem>
                    <MenuItem value="BANK">Bank Transfer</MenuItem>
                  </TextField>

                  <TextField
                    fullWidth
                    label="Customer Info (Optional)"
                    value={customerInfo}
                    onChange={(e) => setCustomerInfo(e.target.value)}
                    placeholder="Customer name or phone"
                    sx={{ mb: 2 }}
                    size="small"
                  />

                  <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    onClick={handleCheckout}
                    disabled={processing}
                    startIcon={processing ? <CircularProgress size={20} /> : null}
                  >
                    {processing ? 'Processing...' : 'Complete Sale'}
                  </Button>

                  <Button
                    fullWidth
                    variant="outlined"
                    size="small"
                    onClick={() => setCart([])}
                    sx={{ mt: 1 }}
                    disabled={processing}
                  >
                    Clear Cart
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Agent Distribution Info Panel - shown when agent tab is active */}
      {activeTab === 1 && (
        <Paper sx={{ p: 3, mt: 3, bgcolor: 'success.light' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <TransferIcon sx={{ fontSize: 40, color: 'success.dark' }} />
            <div>
              <Typography variant="h6" fontWeight="bold" color="success.dark">
                Field Agent Distribution
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Give products to field agents who will sell on your behalf
              </Typography>
            </div>
          </Box>
          <Divider sx={{ my: 2 }} />
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>How it works:</strong>
          </Typography>
          <Typography variant="body2" component="div" sx={{ pl: 2 }}>
            • Select an agent and products to distribute<br />
            • Stock is transferred from your shop to the agent's inventory<br />
            • Amount is added to the agent's debt ledger<br />
            • Agent sells products in the field and pays you back<br />
            • Track all agent debts and payments in the Agents section
          </Typography>
          <Button
            variant="contained"
            color="success"
            size="large"
            startIcon={<TransferIcon />}
            onClick={() => setOpenTransferDialog(true)}
            sx={{ mt: 2 }}
          >
            Transfer Stock to Agent
          </Button>
        </Paper>
      )}

      <Suspense fallback={null}>
        <StockTransferDialog
          open={openTransferDialog}
          onClose={() => setOpenTransferDialog(false)}
          onSuccess={() => {
            loadProducts();
            setSuccess('Stock transferred to agent successfully!');
          }}
        />
      </Suspense>
    </Box>
  );
}
