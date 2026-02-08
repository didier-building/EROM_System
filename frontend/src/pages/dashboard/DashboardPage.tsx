/**
 * Dashboard page - Main overview
 */
import { useEffect, useState, useMemo, useCallback, lazy, Suspense } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Divider,
  IconButton,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  Warning,
  People,
  TrendingUp,
  AttachMoney,
  SwapHoriz as TransferIcon,
  Receipt as ReceiptIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { salesApi, inventoryApi } from '../../api';
import { useAuthStore } from '../../store';
import type { DashboardStats, Product } from '../../types';

const StockTransferDialog = lazy(() => import('../../components/agents/StockTransferDialog'));

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}

function StatCard({ title, value, icon, color, subtitle }: StatCardProps) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold">
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: 2,
              bgcolor: `${color}.light`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const location = useLocation();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openTransferDialog, setOpenTransferDialog] = useState(false);
  const [lowStockProducts, setLowStockProducts] = useState<Product[]>([]);
  const [recentTransactions, setRecentTransactions] = useState<any[]>([]);
  
  const isOwner = useMemo(() => user?.role === 'owner', [user?.role]);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Load stats
      const statsResponse = await salesApi.getDashboardStats();
      setStats(statsResponse.data);
      
      // Load low stock products
      const productsResponse = await inventoryApi.getProducts();
      const lowStock = productsResponse.results.filter(
        (p: Product) => p.quantity_in_stock <= (p.reorder_level || 5)
      ).slice(0, 5); // Top 5 low stock items
      setLowStockProducts(lowStock);
      
      // Load today's transactions
      const todayResponse = await salesApi.getTodaySales();
      setRecentTransactions(todayResponse.data.transactions.slice(0, 5));
      
    } catch (err: any) {
      console.error('Dashboard error:', err);
      setError(err.response?.data?.message || err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Refresh dashboard when navigating to it
  useEffect(() => {
    if (location.pathname === '/dashboard') {
      loadDashboardData();
    }
  }, [location, loadDashboardData]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <div>
          <Typography variant="h4" fontWeight="bold">
            Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Welcome back, {user?.full_name}! Here's what's happening today.
          </Typography>
        </div>
        <IconButton 
          onClick={loadDashboardData} 
          disabled={loading}
          color="primary"
          size="large"
          title="Refresh dashboard"
        >
          <RefreshIcon />
        </IconButton>
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {/* Today's Sales */}
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' } }}>
          <StatCard
            title="Today's Sales"
            value={`${parseInt(stats?.today_sales || '0').toLocaleString()} RWF`}
            subtitle={`${stats?.today_transactions || 0} transactions`}
            icon={<AttachMoney sx={{ fontSize: 32, color: 'success.main' }} />}
            color="success"
          />
        </Box>

        {/* Total Products */}
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' } }}>
          <StatCard
            title="Total Products"
            value={stats?.total_products || 0}
            subtitle="In inventory"
            icon={<InventoryIcon sx={{ fontSize: 32, color: 'primary.main' }} />}
            color="primary"
          />
        </Box>

        {/* Low Stock Products */}
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' } }}>
          <StatCard
            title="Low Stock"
            value={stats?.low_stock_products || 0}
            subtitle="Need reorder"
            icon={<Warning sx={{ fontSize: 32, color: 'warning.main' }} />}
            color="warning"
          />
        </Box>

        {/* Total Agents */}
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(25% - 18px)' } }}>
          <StatCard
            title="Active Agents"
            value={stats?.total_agents || 0}
            subtitle={isOwner ? `${parseInt(stats?.total_debt || '0').toLocaleString()} RWF debt` : 'Field agents'}
            icon={<People sx={{ fontSize: 32, color: 'info.main' }} />}
            color="info"
          />
        </Box>

        {/* Inventory Value - Owner Only */}
        {isOwner && (
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' } }}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <TrendingUp color="success" />
                <Typography variant="h6" fontWeight="bold">
                  Total Inventory Value
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" color="success.main">
                {parseInt(stats?.inventory_value || '0').toLocaleString()} RWF
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Total value of all products in stock
              </Typography>
            </Paper>
          </Box>
        )}

        {/* Quick Actions */}
        <Box sx={{ flex: { xs: '1 1 100%', md: isOwner ? '1 1 calc(50% - 12px)' : '1 1 100%' } }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
              <Card sx={{ bgcolor: 'success.light' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    <TransferIcon sx={{ color: 'success.dark', fontSize: 28 }} />
                    <Typography variant="subtitle1" fontWeight="bold" color="success.dark">
                      Field Distribution
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Give products to field agents who sell on your behalf and pay you back
                  </Typography>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<TransferIcon />}
                    onClick={() => setOpenTransferDialog(true)}
                    fullWidth
                  >
                    Distribute to Agent
                  </Button>
                </CardContent>
              </Card>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, px: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  • Process cash sales at POS
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • Add new products to inventory
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • Manage agent accounts & payments
                </Typography>
                {isOwner && (
                  <Typography variant="body2" color="text.secondary">
                    • View detailed business reports
                  </Typography>
                )}
              </Box>
            </Box>
          </Paper>
        </Box>
      </Box>

      {/* Recent Activity Section */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mt: 4 }}>
        {/* Recent Transactions */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' } }}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ReceiptIcon color="primary" />
                <Typography variant="h6" fontWeight="bold">
                  Today's Transactions
                </Typography>
              </Box>
              <Chip label={recentTransactions.length} color="primary" size="small" />
            </Box>
            
            {recentTransactions.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography color="text.secondary">
                  No transactions today yet
                </Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Time</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Amount</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentTransactions.map((transaction) => (
                      <TableRow key={transaction.id} hover>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(transaction.transaction_date).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={transaction.payment_method}
                            size="small"
                            color={transaction.payment_method === 'CASH' ? 'success' : 'info'}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="medium" color="success.main">
                            {parseInt(transaction.total_amount).toLocaleString()} RWF
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Box>

        {/* Low Stock Alert */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' } }}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Warning color="warning" />
                <Typography variant="h6" fontWeight="bold">
                  Low Stock Alert
                </Typography>
              </Box>
              <Chip label={lowStockProducts.length} color="warning" size="small" />
            </Box>
            
            {lowStockProducts.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography color="text.secondary">
                  All products are well stocked! 🎉
                </Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Product</TableCell>
                      <TableCell align="center">Stock</TableCell>
                      <TableCell align="center">Min</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {lowStockProducts.map((product) => (
                      <TableRow key={product.id} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {product.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {product.sku}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={product.quantity_in_stock}
                            size="small"
                            color={product.quantity_in_stock === 0 ? 'error' : 'warning'}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" color="text.secondary">
                            {product.reorder_level || 5}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Box>
      </Box>

      <Suspense fallback={null}>
        <StockTransferDialog
          open={openTransferDialog}
          onClose={() => setOpenTransferDialog(false)}
          onSuccess={() => {
            loadDashboardData(); // Refresh stats after transfer
          }}
        />
      </Suspense>
    </Box>
  );
}
