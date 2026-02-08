/**
 * AddAgentDialog - Dialog for adding new agents
 */
import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Alert,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import { agentsApi } from '../../api';

interface AddAgentDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AddAgentDialog({ open, onClose, onSuccess }: AddAgentDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    id_number: '',
    address: '',
    area: '',
    business_name: '',
    credit_limit: '',
    is_trusted: false,
    notes: '',
  });

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [field]: e.target.value });
  };

  const handleCheckboxChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [field]: e.target.checked });
  };

  const handleSubmit = async () => {
    setError(null);
    
    // Validation
    if (!formData.full_name || !formData.phone_number || !formData.credit_limit) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      await agentsApi.createAgent({
        full_name: formData.full_name,
        phone_number: formData.phone_number,
        id_number: formData.id_number || undefined,
        address: formData.address || undefined,
        area: formData.area || undefined,
        business_name: formData.business_name || undefined,
        credit_limit: parseFloat(formData.credit_limit),
        is_trusted: formData.is_trusted,
        notes: formData.notes || undefined,
      });
      
      // Reset form
      setFormData({
        full_name: '',
        phone_number: '',
        id_number: '',
        address: '',
        area: '',
        business_name: '',
        credit_limit: '',
        is_trusted: false,
        notes: '',
      });
      
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create agent');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Add New Agent</DialogTitle>
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
                label="Full Name"
                value={formData.full_name}
                onChange={handleChange('full_name')}
                required
              />
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Phone Number"
                value={formData.phone_number}
                onChange={handleChange('phone_number')}
                required
              />
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="ID Number"
                value={formData.id_number}
                onChange={handleChange('id_number')}
              />
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Area/Location"
                value={formData.area}
                onChange={handleChange('area')}
              />
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Business Name"
                value={formData.business_name}
                onChange={handleChange('business_name')}
              />
            </Box>
            
            <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '200px' }}>
              <TextField
                fullWidth
                label="Credit Limit (RWF)"
                type="number"
                value={formData.credit_limit}
                onChange={handleChange('credit_limit')}
                required
                helperText="Enter 0 for unlimited credit"
              />
            </Box>
          </Box>
          
          <Box>
            <TextField
              fullWidth
              label="Address"
              value={formData.address}
              onChange={handleChange('address')}
            />
          </Box>
          
          <Box>
            <TextField
              fullWidth
              label="Notes"
              multiline
              rows={3}
              value={formData.notes}
              onChange={handleChange('notes')}
            />
          </Box>
          
          <Box>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.is_trusted}
                  onChange={handleCheckboxChange('is_trusted')}
                />
              }
              label="Trusted Agent (can have higher credit limits)"
            />
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} variant="contained" disabled={loading}>
          {loading ? 'Adding...' : 'Add Agent'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
