/**
 * AgentDetailsDialog - View agent's stock transfers and debt details
 */
import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
  Chip,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import { agentsApi } from '../../api';
import type { Agent, AgentLedger } from '../../types';

interface AgentDetailsDialogProps {
  open: boolean;
  onClose: () => void;
  agent: Agent | null;
}

export default function AgentDetailsDialog({ open, onClose, agent }: AgentDetailsDialogProps) {
  const [ledger, setLedger] = useState<AgentLedger[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && agent) {
      loadLedger();
    }
  }, [open, agent]);

  const loadLedger = async () => {
    if (!agent) return;
    
    try {
      setLoading(true);
      const data = await agentsApi.getAgentLedger(agent.id);
      setLedger(data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load agent ledger');
    } finally {
      setLoading(false);
    }
  };

  if (!agent) return null;

  const unpaidLedger = ledger.filter(entry => !entry.is_paid);
  const paidLedger = ledger.filter(entry => entry.is_paid);
  const totalUnpaid = unpaidLedger.reduce((sum, entry) => sum + parseFloat(entry.debt_amount), 0);
  const totalPaid = paidLedger.reduce((sum, entry) => sum + parseFloat(entry.paid_amount), 0);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box>
          <Typography variant="h6">{agent.full_name}</Typography>
          <Typography variant="body2" color="text.secondary">
            {agent.phone_number} • {agent.area || 'N/A'}
          </Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Summary Cards */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Box sx={{ flex: 1, p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
            <Typography variant="body2" color="error.dark">
              Total Unpaid Debt
            </Typography>
            <Typography variant="h5" fontWeight="bold" color="error.dark">
              {totalUnpaid.toLocaleString()} RWF
            </Typography>
            <Typography variant="caption" color="error.dark">
              {unpaidLedger.length} unpaid items
            </Typography>
          </Box>
          
          <Box sx={{ flex: 1, p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
            <Typography variant="body2" color="success.dark">
              Total Paid
            </Typography>
            <Typography variant="h5" fontWeight="bold" color="success.dark">
              {totalPaid.toLocaleString()} RWF
            </Typography>
            <Typography variant="caption" color="success.dark">
              {paidLedger.length} paid items
            </Typography>
          </Box>
          
          <Box sx={{ flex: 1, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
            <Typography variant="body2" color="info.dark">
              Credit Limit
            </Typography>
            <Typography variant="h5" fontWeight="bold" color="info.dark">
              {parseFloat(agent.credit_limit).toLocaleString()} RWF
            </Typography>
            <Typography variant="caption" color="info.dark">
              {agent.can_take_more_stock ? 'Can take more' : 'Limit reached'}
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Unpaid Stock */}
            {unpaidLedger.length > 0 && (
              <>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Unpaid Stock ({unpaidLedger.length} items)
                </Typography>
                <TableContainer sx={{ mb: 3 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Product</TableCell>
                        <TableCell align="right">Quantity</TableCell>
                        <TableCell align="right">Unit Price</TableCell>
                        <TableCell align="right">Total Debt</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {unpaidLedger.map((entry) => (
                        <TableRow key={entry.id}>
                          <TableCell>
                            {new Date(entry.transfer_date).toLocaleDateString()}
                          </TableCell>
                          <TableCell>{entry.product_name}</TableCell>
                          <TableCell align="right">{entry.quantity}</TableCell>
                          <TableCell align="right">
                            {parseFloat(entry.unit_price).toLocaleString()} RWF
                          </TableCell>
                          <TableCell align="right">
                            <Typography fontWeight="bold" color="error">
                              {parseFloat(entry.debt_amount).toLocaleString()} RWF
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label="Unpaid" color="error" size="small" />
                          </TableCell>
                        </TableRow>
                      ))}
                      <TableRow>
                        <TableCell colSpan={4} align="right">
                          <Typography fontWeight="bold">Total Unpaid:</Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold" color="error">
                            {totalUnpaid.toLocaleString()} RWF
                          </Typography>
                        </TableCell>
                        <TableCell />
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}

            {/* Paid Stock */}
            {paidLedger.length > 0 && (
              <>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Paid Stock History ({paidLedger.length} items)
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Transfer Date</TableCell>
                        <TableCell>Product</TableCell>
                        <TableCell align="right">Quantity</TableCell>
                        <TableCell align="right">Unit Price</TableCell>
                        <TableCell align="right">Amount Paid</TableCell>
                        <TableCell>Payment Date</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {paidLedger.map((entry) => (
                        <TableRow key={entry.id}>
                          <TableCell>
                            {new Date(entry.transfer_date).toLocaleDateString()}
                          </TableCell>
                          <TableCell>{entry.product_name}</TableCell>
                          <TableCell align="right">{entry.quantity}</TableCell>
                          <TableCell align="right">
                            {parseFloat(entry.unit_price).toLocaleString()} RWF
                          </TableCell>
                          <TableCell align="right">
                            {parseFloat(entry.paid_amount).toLocaleString()} RWF
                          </TableCell>
                          <TableCell>
                            {entry.payment_date
                              ? new Date(entry.payment_date).toLocaleDateString()
                              : '-'}
                          </TableCell>
                          <TableCell>
                            <Chip label="Paid" color="success" size="small" />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}

            {ledger.length === 0 && !loading && (
              <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
                No stock transfers yet for this agent.
              </Typography>
            )}
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
