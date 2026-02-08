/**
 * StockTransferDialog - Transfer stock to agents
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
  Typography,
  Alert,
  CircularProgress,
  Divider,
  Chip,
} from '@mui/material';
import { inventoryApi, agentsApi } from '../../api';
import type { Product, Agent } from '../../types';

interface StockTransferDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  preselectedAgent?: Agent | null;
}

export default function StockTransferDialog({
  open,
  onClose,
  onSuccess,
  preselectedAgent = null,
}: StockTransferDialogProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    agent_id: preselectedAgent?.id || '',
    product_id: '',
    quantity: '',
    unit_price: '',
    notes: '',
  });

  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(preselectedAgent);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  useEffect(() => {
    if (open) {
      loadData();
      if (preselectedAgent) {
        setFormData((prev) => ({ ...prev, agent_id: String(preselectedAgent.id) }));
        setSelectedAgent(preselectedAgent);
      }
    } else {
      // Reset form when dialog closes
      setFormData({
        agent_id: '',
        product_id: '',
        quantity: '',
        unit_price: '',
        notes: '',
      });
      setSelectedAgent(null);
      setSelectedProduct(null);
      setError(null);
    }
  }, [open, preselectedAgent]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [agentsResponse, productsResponse] = await Promise.all([
        agentsApi.getAgents(),
        inventoryApi.getProducts(),
      ]);

      console.log('Agents response:', agentsResponse);
      console.log('Products response:', productsResponse);

      // Only show active agents who can take more stock
      const eligibleAgents = agentsResponse.results.filter(
        (a) => a.is_active && a.can_take_more_stock
      );
      setAgents(eligibleAgents);
      console.log('Eligible agents:', eligibleAgents);

      // Only show products with stock available
      const availableProducts = productsResponse.results.filter(
        (p) => p.quantity_in_stock > 0 && p.is_active
      );
      setProducts(availableProducts);
      console.log('Available products:', availableProducts);

      if (eligibleAgents.length === 0) {
        setError('No agents available. All agents have reached their credit limit or are inactive.');
      }
      if (availableProducts.length === 0) {
        setError('No products available in stock.');
      }
    } catch (err: any) {
      console.error('Load data error:', err);
      setError(err.response?.data?.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleAgentChange = (agentId: string) => {
    const agent = agents.find((a) => a.id === parseInt(agentId));
    setSelectedAgent(agent || null);
    setFormData({ ...formData, agent_id: agentId });
  };

  const handleProductChange = (productId: string) => {
    const product = products.find((p) => p.id === parseInt(productId));
    setSelectedProduct(product || null);
    setFormData({
      ...formData,
      product_id: productId,
      unit_price: product?.selling_price || '',
    });
  };

  const calculateDebtAmount = () => {
    const quantity = parseInt(formData.quantity) || 0;
    const unitPrice = parseFloat(formData.unit_price) || 0;
    return quantity * unitPrice;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.agent_id || !formData.product_id || !formData.quantity || !formData.unit_price) {
      setError('Please fill in all required fields');
      return;
    }

    const quantity = parseInt(formData.quantity);
    if (selectedProduct && quantity > selectedProduct.quantity_in_stock) {
      setError(`Only ${selectedProduct.quantity_in_stock} units available in stock`);
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      await agentsApi.transferStock(parseInt(formData.agent_id), {
        product_id: parseInt(formData.product_id),
        quantity: quantity,
        unit_price: parseFloat(formData.unit_price),
        debt_amount: calculateDebtAmount(),
        notes: formData.notes || '',
      });

      setFormData({
        agent_id: preselectedAgent?.id || '',
        product_id: '',
        quantity: '',
        unit_price: '',
        notes: '',
      });
      setSelectedProduct(null);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to transfer stock');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!submitting) {
      setFormData({
        agent_id: preselectedAgent ? String(preselectedAgent.id) : '',
        product_id: '',
        quantity: '',
        unit_price: '',
        notes: '',
      });
      setSelectedAgent(preselectedAgent);
      setSelectedProduct(null);
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>Transfer Stock to Agent</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <TextField
                select
                fullWidth
                label="Select Agent"
                value={formData.agent_id}
                onChange={(e) => handleAgentChange(e.target.value)}
                required
                disabled={!!preselectedAgent}
                sx={{ mb: 2, mt: 1 }}
                helperText={agents.length === 0 ? 'No agents available for stock transfer' : ''}
              >
                <MenuItem value="">
                  <em>Choose an agent...</em>
                </MenuItem>
                {agents.length === 0 ? (
                  <MenuItem value="" disabled>
                    No eligible agents found
                  </MenuItem>
                ) : (
                  agents.map((agent) => (
                    <MenuItem key={agent.id} value={agent.id}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                        <span>{agent.full_name}</span>
                        <Chip
                          label={`Debt: ${parseFloat(agent.total_debt).toLocaleString()} RWF`}
                          size="small"
                          color={parseFloat(agent.total_debt) > 0 ? 'warning' : 'success'}
                        />
                      </Box>
                    </MenuItem>
                  ))
                )}
              </TextField>

              {selectedAgent && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Credit Limit:</strong> {parseFloat(selectedAgent.credit_limit).toLocaleString()} RWF
                  </Typography>
                  <Typography variant="body2">
                    <strong>Current Debt:</strong> {parseFloat(selectedAgent.total_debt).toLocaleString()} RWF
                  </Typography>
                  <Typography variant="body2">
                    <strong>Available Credit:</strong>{' '}
                    {(parseFloat(selectedAgent.credit_limit) - parseFloat(selectedAgent.total_debt)).toLocaleString()}{' '}
                    RWF
                  </Typography>
                </Alert>
              )}

              <TextField
                select
                fullWidth
                label="Select Product"
                value={formData.product_id}
                onChange={(e) => handleProductChange(e.target.value)}
                required
                sx={{ mb: 2 }}
                helperText={products.length === 0 ? 'No products available in stock' : ''}
              >
                <MenuItem value="">
                  <em>Choose a product...</em>
                </MenuItem>
                {products.length === 0 ? (
                  <MenuItem value="" disabled>
                    No products with available stock
                  </MenuItem>
                ) : (
                  products.map((product) => (
                    <MenuItem key={product.id} value={product.id}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                        <span>
                          {product.name} ({product.sku})
                        </span>
                        <Chip label={`Stock: ${product.quantity_in_stock}`} size="small" color="primary" />
                      </Box>
                    </MenuItem>
                  ))
                )}
              </TextField>

              {selectedProduct && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Available Stock:</strong> {selectedProduct.quantity_in_stock} units
                  </Typography>
                  <Typography variant="body2">
                    <strong>Selling Price:</strong> {parseFloat(selectedProduct.selling_price).toLocaleString()} RWF
                  </Typography>
                </Alert>
              )}

              <TextField
                fullWidth
                label="Quantity"
                type="number"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                required
                inputProps={{ min: 1, max: selectedProduct?.quantity_in_stock || 1000 }}
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Unit Price (RWF)"
                type="number"
                value={formData.unit_price}
                onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                required
                inputProps={{ min: 0, step: 0.01 }}
                sx={{ mb: 2 }}
              />

              {formData.quantity && formData.unit_price && (
                <Box sx={{ p: 2, bgcolor: 'primary.light', borderRadius: 1, mb: 2 }}>
                  <Typography variant="h6" color="primary.contrastText" textAlign="center">
                    Total Debt: {calculateDebtAmount().toLocaleString()} RWF
                  </Typography>
                </Box>
              )}

              <TextField
                fullWidth
                label="Notes (Optional)"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                multiline
                rows={2}
              />
            </>
          )}
        </DialogContent>
        <Divider />
        <DialogActions>
          <Button onClick={handleClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={loading || submitting}>
            {submitting ? <CircularProgress size={24} /> : 'Transfer Stock'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
