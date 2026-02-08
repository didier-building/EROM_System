/**
 * AgentsPage - Agent management
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
  Card,
  CardContent,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  SwapHoriz as TransferIcon,
} from '@mui/icons-material';
import { agentsApi } from '../../api';
import type { Agent } from '../../types';

const AddAgentDialog = lazy(() => import('../../components/agents/AddAgentDialog'));
const AgentDetailsDialog = lazy(() => import('../../components/agents/AgentDetailsDialog'));
const EditAgentDialog = lazy(() => import('../../components/agents/EditAgentDialog'));
const StockTransferDialog = lazy(() => import('../../components/agents/StockTransferDialog'));

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [openDetailsDialog, setOpenDetailsDialog] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [openTransferDialog, setOpenTransferDialog] = useState(false);
  const [transferAgent, setTransferAgent] = useState<Agent | null>(null);

  const loadAgents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await agentsApi.getAgents();
      setAgents(response.results);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAgents();
  }, [loadAgents]);

  const handleViewDetails = useCallback((agent: Agent) => {
    setSelectedAgent(agent);
    setOpenDetailsDialog(true);
  }, []);

  const handleEdit = useCallback((agent: Agent) => {
    setEditingAgent(agent);
    setOpenEditDialog(true);
  }, []);

  const handleTransfer = useCallback((agent: Agent) => {
    setTransferAgent(agent);
    setOpenTransferDialog(true);
  }, []);

  const filteredAgents = useMemo(() => {
    if (!searchQuery) return agents;
    const query = searchQuery.toLowerCase();
    return agents.filter(
      (agent) =>
        agent.full_name.toLowerCase().includes(query) ||
        agent.phone_number.includes(searchQuery) ||
        (agent.area && agent.area.toLowerCase().includes(query))
    );
  }, [agents, searchQuery]);

  const totalDebt = useMemo(
    () => agents.reduce((sum, agent) => sum + parseFloat(agent.total_debt || '0'), 0),
    [agents]
  );
  const activeAgents = useMemo(
    () => agents.filter((agent) => agent.is_active).length,
    [agents]
  );

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
            Agents Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage sales agents and their accounts
          </Typography>
        </div>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />} 
          size="large"
          onClick={() => setOpenAddDialog(true)}
        >
          Add Agent
        </Button>
      </Box>

      <AddAgentDialog
        open={openAddDialog}
        onClose={() => setOpenAddDialog(false)}
        onSuccess={loadAgents}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(33.33% - 11px)' } }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Agents
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                {agents.length}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {activeAgents} active
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(33.33% - 11px)' } }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Debt
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="error">
                {totalDebt.toLocaleString()} RWF
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Across all agents
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(33.33% - 11px)' } }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Average Debt
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                {agents.length > 0 ? Math.round(totalDebt / agents.length).toLocaleString() : 0} RWF
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Per agent
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search agents by name, phone, or location..."
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
              <TableCell>Agent Name</TableCell>
              <TableCell>Phone Number</TableCell>
              <TableCell>Location</TableCell>
              <TableCell align="right">Credit Limit</TableCell>
              <TableCell align="right">Total Debt</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredAgents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary" sx={{ py: 4 }}>
                    {searchQuery ? 'No agents found' : 'No agents yet. Add your first agent!'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredAgents.map((agent) => {
                const debt = parseFloat(agent.total_debt || '0');
                const creditLimit = parseFloat(agent.credit_limit);
                const hasDebt = debt > 0;
                const nearLimit = debt >= creditLimit * 0.8;

                return (
                  <TableRow key={agent.id} hover>
                    <TableCell>
                      <Typography fontWeight="medium">{agent.full_name}</Typography>
                    </TableCell>
                    <TableCell>{agent.phone_number}</TableCell>
                    <TableCell>{agent.area || '-'}</TableCell>
                    <TableCell align="right">{creditLimit.toLocaleString()}</TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                        {nearLimit && hasDebt && <WarningIcon color="warning" fontSize="small" />}
                        <Typography color={hasDebt ? 'error' : 'text.primary'}>
                          {debt.toLocaleString()}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {agent.is_active ? (
                        <Chip
                          label="Active"
                          color="success"
                          size="small"
                          icon={<CheckIcon />}
                        />
                      ) : (
                        <Chip label="Inactive" color="default" size="small" />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" color="primary" onClick={() => handleViewDetails(agent)}>
                        <ViewIcon fontSize="small" />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        color="success" 
                        onClick={() => handleTransfer(agent)}
                        disabled={!agent.can_take_more_stock}
                        title={agent.can_take_more_stock ? 'Transfer stock' : 'Credit limit reached'}
                      >
                        <TransferIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" color="primary" onClick={() => handleEdit(agent)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Suspense fallback={null}>
        <AddAgentDialog
          open={openAddDialog}
          onClose={() => setOpenAddDialog(false)}
          onSuccess={loadAgents}
        />

        <AgentDetailsDialog
          open={openDetailsDialog}
          onClose={() => {
            setOpenDetailsDialog(false);
            setSelectedAgent(null);
          }}
          agent={selectedAgent}
        />

        <EditAgentDialog
          open={openEditDialog}
          onClose={() => {
            setOpenEditDialog(false);
            setEditingAgent(null);
          }}
          onSuccess={loadAgents}
          agent={editingAgent}
        />

        <StockTransferDialog
          open={openTransferDialog}
          onClose={() => {
            setOpenTransferDialog(false);
            setTransferAgent(null);
          }}
          onSuccess={loadAgents}
          preselectedAgent={transferAgent}
        />
      </Suspense>
    </Box>
  );
}
