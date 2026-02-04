import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import LoadingSpinner from "./LoadingSpinner";

export default function ProtectedRoute({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, emailVerified, hasProfile } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (emailVerified === false) {
    return <Navigate to="/verify-email" replace />;
  }

  if (hasProfile === false) {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
}
