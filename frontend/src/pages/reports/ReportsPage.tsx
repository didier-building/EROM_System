/**
 * ReportsPage - Reports and analytics
 */
import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Paper,
  Tabs,
  Tab,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Chip,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingIcon,
  Inventory as InventoryIcon,
  People as PeopleIcon,
  Download as DownloadIcon,
  DateRange as DateRangeIcon,
} from '@mui/icons-material';
import { format, subDays } from 'date-fns';
import { salesApi, inventoryApi, agentsApi } from '../../api';
import type { Transaction, Product, Agent } from '../../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`report-tabpanel-${index}`}
      aria-labelledby={`report-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [startDate, setStartDate] = useState(format(subDays(new Date(), 30), 'yyyy-MM-dd'));
  const [endDate, setEndDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);

  // Sales stats
  const [salesStats, setSalesStats] = useState({
    totalSales: 0,
    totalTransactions: 0,
    averageSale: 0,
    cashSales: 0,
    creditSales: 0,
  });

  // Inventory stats
  const [inventoryStats, setInventoryStats] = useState({
    totalProducts: 0,
    totalValue: 0,
    lowStock: 0,
    outOfStock: 0,
  });

  // Agent stats
  const [agentStats, setAgentStats] = useState({
    totalAgents: 0,
    totalDebt: 0,
    activeAgents: 0,
  });

  useEffect(() => {
    loadReportData();
  }, [startDate, endDate, activeTab]);

  const loadReportData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (activeTab === 0) {
        // Load sales data
        const response = await salesApi.getTransactions();
        
        const filteredTransactions = response.results.filter((t) => {
          const txDate = new Date(t.transaction_date).toISOString().split('T')[0];
          return txDate >= startDate && txDate <= endDate;
        });
        
        setTransactions(filteredTransactions);

        // Calculate sales stats
        const total = filteredTransactions.reduce((sum, t) => {
          return sum + parseFloat(t.total_amount);
        }, 0);
        
        const cash = filteredTransactions
          .filter((t) => t.payment_method.toLowerCase() === 'cash')
          .reduce((sum, t) => sum + parseFloat(t.total_amount), 0);
        const credit = filteredTransactions
          .filter((t) => t.payment_method.toLowerCase() === 'credit')
          .reduce((sum, t) => sum + parseFloat(t.total_amount), 0);

        setSalesStats({
          totalSales: total,
          totalTransactions: filteredTransactions.length,
          averageSale: filteredTransactions.length > 0 ? total / filteredTransactions.length : 0,
          cashSales: cash,
          creditSales: credit,
        });
      } else if (activeTab === 1) {
        // Load inventory data
        const response = await inventoryApi.getProducts();
        setProducts(response.results);

        const totalValue = response.results.reduce(
          (sum, p) => sum + parseFloat(p.selling_price) * p.quantity_in_stock,
          0
        );
        const lowStock = response.results.filter((p) => p.quantity_in_stock <= p.reorder_level).length;
        const outOfStock = response.results.filter((p) => p.quantity_in_stock === 0).length;

        setInventoryStats({
          totalProducts: response.results.length,
          totalValue: totalValue,
          lowStock: lowStock,
          outOfStock: outOfStock,
        });
      } else if (activeTab === 2) {
        // Load agent data
        const response = await agentsApi.getAgents();
        setAgents(response.results);

        const totalDebt = response.results.reduce((sum, a) => sum + parseFloat(a.total_debt), 0);
        const active = response.results.filter((a) => a.is_active).length;

        setAgentStats({
          totalAgents: response.results.length,
          totalDebt: totalDebt,
          activeAgents: active,
        });
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load report data');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (type: 'excel' | 'pdf') => {
    // Create CSV data for Excel export
    if (type === 'excel') {
      let csvContent = '';
      let filename = '';

      if (activeTab === 0) {
        // Sales Report CSV
        csvContent = 'Date,Transaction ID,Type,Amount,Payment Method,Customer\n';
        transactions.forEach((t) => {
          csvContent += `${format(new Date(t.transaction_date), 'yyyy-MM-dd HH:mm')},${t.transaction_id},${t.transaction_type},${t.total_amount},${t.payment_method},${t.customer_name || 'N/A'}\n`;
        });
        filename = `sales-report-${startDate}-to-${endDate}.csv`;
      } else if (activeTab === 1) {
        // Inventory Report CSV
        csvContent = 'Product,SKU,Category,Brand,Stock,Price,Value,Status\n';
        products.forEach((p) => {
          const value = parseFloat(p.selling_price) * p.quantity_in_stock;
          const status = p.quantity_in_stock === 0 ? 'Out of Stock' : p.quantity_in_stock <= p.reorder_level ? 'Low Stock' : 'In Stock';
          csvContent += `${p.name},${p.sku},${p.category_name || 'N/A'},${p.brand_name || 'N/A'},${p.quantity_in_stock},${p.selling_price},${value},${status}\n`;
        });
        filename = `inventory-report-${format(new Date(), 'yyyy-MM-dd')}.csv`;
      } else if (activeTab === 2) {
        // Agent Report CSV
        csvContent = 'Name,Phone,Area,Debt,Credit Limit,Status\n';
        agents.forEach((a) => {
          csvContent += `${a.full_name},${a.phone_number},${a.area || 'N/A'},${a.total_debt},${a.credit_limit},${a.is_active ? 'Active' : 'Inactive'}\n`;
        });
        filename = `agent-report-${format(new Date(), 'yyyy-MM-dd')}.csv`;
      }

      // Create and download CSV file
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      link.click();
    } else {
      alert('PDF export feature coming soon!');
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Reports & Analytics
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Comprehensive business insights and data analysis
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
          <Tab icon={<TrendingIcon />} label="Sales Reports" />
          <Tab icon={<InventoryIcon />} label="Inventory Reports" />
          <Tab icon={<PeopleIcon />} label="Agent Reports" />
        </Tabs>
      </Paper>

      {/* Date Range Filter (for sales only) */}
      {activeTab === 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
            <DateRangeIcon color="action" />
            <TextField
              label="Start Date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              size="small"
            />
            <TextField
              label="End Date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              size="small"
            />
            <Button variant="outlined" onClick={loadReportData} disabled={loading}>
              Apply Filter
            </Button>
          </Box>
        </Paper>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Sales Report Tab */}
          <TabPanel value={activeTab} index={0}>
            {/* Sales Summary Cards */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3 }}>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Total Sales
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="primary">
                    {salesStats.totalSales.toLocaleString()} RWF
                  </Typography>
                </CardContent>
              </Card>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Transactions
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {salesStats.totalTransactions}
                  </Typography>
                </CardContent>
              </Card>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Average Sale
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="success.main">
                    {salesStats.averageSale.toLocaleString()} RWF
                  </Typography>
                </CardContent>
              </Card>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3 }}>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Cash Sales
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {salesStats.cashSales.toLocaleString()} RWF
                  </Typography>
                </CardContent>
              </Card>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Credit Sales
                  </Typography>
                  <Typography variant="h5" fontWeight="bold" color="warning.main">
                    {salesStats.creditSales.toLocaleString()} RWF
                  </Typography>
                </CardContent>
              </Card>
            </Box>

            {/* Sales Transactions Table */}
            <Paper>
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" fontWeight="bold">
                  Sales Transactions
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={() => handleExport('excel')}
                  size="small"
                >
                  Export to CSV
                </Button>
              </Box>
              <Divider />
              <TableContainer sx={{ maxHeight: 500 }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Transaction ID</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell>Payment</TableCell>
                      <TableCell>Customer</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {transactions.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} align="center">
                          <Typography color="text.secondary" sx={{ py: 4 }}>
                            No transactions found for the selected period
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      transactions.map((t) => (
                        <TableRow key={t.id} hover>
                          <TableCell>{format(new Date(t.transaction_date), 'MMM dd, yyyy HH:mm')}</TableCell>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {t.transaction_id}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={t.transaction_type}
                              size="small"
                              color={t.transaction_type.toUpperCase() === 'SALE' ? 'success' : 'default'}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography fontWeight="bold">{parseFloat(t.total_amount).toLocaleString()} RWF</Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={t.payment_method.replace('_', ' ')}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>{t.customer_name || '-'}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </TabPanel>

          {/* Inventory Report Tab */}
          <TabPanel value={activeTab} index={1}>
            {/* Inventory Summary Cards */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3 }}>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Total Products
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="primary">
                    {inventoryStats.totalProducts}
                  </Typography>
                </CardContent>
              </Card>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Inventory Value
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="success.main">
                    {inventoryStats.totalValue.toLocaleString()} RWF
                  </Typography>
                </CardContent>
              </Card>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Low Stock Items
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="warning.main">
                    {inventoryStats.lowStock}
                  </Typography>
                </CardContent>
              </Card>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Out of Stock
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="error.main">
                    {inventoryStats.outOfStock}
                  </Typography>
                </CardContent>
              </Card>
            </Box>

            {/* Inventory Table */}
            <Paper>
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" fontWeight="bold">
                  Product Inventory
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={() => handleExport('excel')}
                  size="small"
                >
                  Export to CSV
                </Button>
              </Box>
              <Divider />
              <TableContainer sx={{ maxHeight: 500 }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Product</TableCell>
                      <TableCell>SKU</TableCell>
                      <TableCell>Category</TableCell>
                      <TableCell align="right">Stock</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell align="right">Value</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {products.map((p) => {
                      const value = parseFloat(p.selling_price) * p.quantity_in_stock;
                      return (
                        <TableRow key={p.id} hover>
                          <TableCell>
                            <Typography fontWeight="medium">{p.name}</Typography>
                          </TableCell>
                          <TableCell>{p.sku}</TableCell>
                          <TableCell>{p.category_name}</TableCell>
                          <TableCell align="right">{p.quantity_in_stock}</TableCell>
                          <TableCell align="right">{parseFloat(p.selling_price).toLocaleString()} RWF</TableCell>
                          <TableCell align="right">
                            <Typography fontWeight="bold">{value.toLocaleString()} RWF</Typography>
                          </TableCell>
                          <TableCell>
                            {p.quantity_in_stock === 0 ? (
                              <Chip label="Out of Stock" color="error" size="small" />
                            ) : p.quantity_in_stock <= p.reorder_level ? (
                              <Chip label="Low Stock" color="warning" size="small" />
                            ) : (
                              <Chip label="In Stock" color="success" size="small" />
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </TabPanel>

          {/* Agent Report Tab */}
          <TabPanel value={activeTab} index={2}>
            {/* Agent Summary Cards */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3 }}>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Total Agents
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="primary">
                    {agentStats.totalAgents}
                  </Typography>
                </CardContent>
              </Card>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Active Agents
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="success.main">
                    {agentStats.activeAgents}
                  </Typography>
                </CardContent>
              </Card>
              <Card sx={{ flex: '1 1 200px' }}>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Total Outstanding Debt
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="error.main">
                    {agentStats.totalDebt.toLocaleString()} RWF
                  </Typography>
                </CardContent>
              </Card>
            </Box>

            {/* Agent Table */}
            <Paper>
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" fontWeight="bold">
                  Agent Performance
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={() => handleExport('excel')}
                  size="small"
                >
                  Export to CSV
                </Button>
              </Box>
              <Divider />
              <TableContainer sx={{ maxHeight: 500 }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Agent Name</TableCell>
                      <TableCell>Phone</TableCell>
                      <TableCell>Area</TableCell>
                      <TableCell align="right">Debt</TableCell>
                      <TableCell align="right">Credit Limit</TableCell>
                      <TableCell>Can Take Stock</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {agents.map((a) => (
                      <TableRow key={a.id} hover>
                        <TableCell>
                          <Typography fontWeight="medium">{a.full_name}</Typography>
                        </TableCell>
                        <TableCell>{a.phone_number}</TableCell>
                        <TableCell>{a.area || '-'}</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold" color={parseFloat(a.total_debt) > 0 ? 'error' : 'inherit'}>
                            {parseFloat(a.total_debt).toLocaleString()} RWF
                          </Typography>
                        </TableCell>
                        <TableCell align="right">{parseFloat(a.credit_limit).toLocaleString()} RWF</TableCell>
                        <TableCell>
                          <Chip
                            label={a.can_take_more_stock ? 'Yes' : 'No'}
                            color={a.can_take_more_stock ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={a.is_active ? 'Active' : 'Inactive'}
                            color={a.is_active ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </TabPanel>
        </>
      )}
    </Box>
  );
}
