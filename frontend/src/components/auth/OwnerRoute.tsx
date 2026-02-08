/**
 * OwnerRoute - Route protection for owner-only pages
 */
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../store';

interface OwnerRouteProps {
  children: React.ReactNode;
}

export default function OwnerRoute({ children }: OwnerRouteProps) {
  const { user, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role !== 'owner') {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
