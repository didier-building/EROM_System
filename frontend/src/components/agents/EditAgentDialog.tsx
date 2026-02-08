/**
 * EditAgentDialog - Dialog for editing existing agents
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
  Alert,
  CircularProgress,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import { agentsApi } from '../../api';
import type { Agent } from '../../types';

interface EditAgentDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  agent: Agent | null;
}

export default function EditAgentDialog({ open, onClose, onSuccess, agent }: EditAgentDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    id_number: '',
    area: '',
    business_name: '',
    credit_limit: '',
    address: '',
    notes: '',
    is_trusted: false,
  });

  useEffect(() => {
    if (open && agent) {
      setFormData({
        full_name: agent.full_name || '',
        phone_number: agent.phone_number || '',
        id_number: agent.id_number || '',
        area: agent.area || '',
        business_name: agent.business_name || '',
        credit_limit: agent.credit_limit?.toString() || '0',
        address: agent.address || '',
        notes: agent.notes || '',
        is_trusted: agent.is_trusted || false,
      });
    }
  }, [open, agent]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked, type } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agent) return;
    
    setError(null);

    // Validation
    if (!formData.full_name || !formData.phone_number || !formData.credit_limit) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      await agentsApi.updateAgent(agent.id, {
        full_name: formData.full_name,
        phone_number: formData.phone_number,
        id_number: formData.id_number || undefined,
        area: formData.area || undefined,
        business_name: formData.business_name || undefined,
        credit_limit: formData.credit_limit,
        address: formData.address || undefined,
        notes: formData.notes || undefined,
        is_trusted: formData.is_trusted,
      });
      
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update agent');
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
        <DialogTitle>Edit Agent</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mt: 1 }}>
            <TextField
              fullWidth
              label="Full Name"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <TextField
              fullWidth
              label="Phone Number"
              name="phone_number"
              value={formData.phone_number}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <TextField
              fullWidth
              label="ID Number"
              name="id_number"
              value={formData.id_number}
              onChange={handleChange}
              disabled={loading}
            />
            <TextField
              fullWidth
              label="Area/Location"
              name="area"
              value={formData.area}
              onChange={handleChange}
              disabled={loading}
            />
            <TextField
              fullWidth
              label="Business Name"
              name="business_name"
              value={formData.business_name}
              onChange={handleChange}
              disabled={loading}
            />
            <TextField
              fullWidth
              label="Credit Limit"
              name="credit_limit"
              type="number"
              value={formData.credit_limit}
              onChange={handleChange}
              required
              disabled={loading}
              inputProps={{ step: '0.01', min: '0' }}
            />
            <TextField
              fullWidth
              label="Address"
              name="address"
              value={formData.address}
              onChange={handleChange}
              multiline
              rows={2}
              disabled={loading}
              sx={{ gridColumn: { sm: '1 / -1' } }}
            />
            <TextField
              fullWidth
              label="Notes"
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              multiline
              rows={2}
              disabled={loading}
              sx={{ gridColumn: { sm: '1 / -1' } }}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.is_trusted}
                  onChange={handleChange}
                  name="is_trusted"
                  disabled={loading}
                />
              }
              label="Trusted Agent (Can exceed credit limit)"
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
            {loading ? 'Updating...' : 'Update Agent'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
