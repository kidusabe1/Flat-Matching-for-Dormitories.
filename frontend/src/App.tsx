import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import OnboardingPage from "./pages/OnboardingPage";
import DashboardPage from "./pages/DashboardPage";
import BrowseListingsPage from "./pages/BrowseListingsPage";
import CreateListingPage from "./pages/CreateListingPage";
import ListingDetailPage from "./pages/ListingDetailPage";
import MyListingsPage from "./pages/MyListingsPage";
import CompatibleSwapsPage from "./pages/CompatibleSwapsPage";
import MatchesPage from "./pages/MatchesPage";
import TransactionsPage from "./pages/TransactionsPage";
import ProfilePage from "./pages/ProfilePage";
import VerifyEmailPage from "./pages/VerifyEmailPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="listings" element={<BrowseListingsPage />} />
          <Route path="listings/new" element={<CreateListingPage />} />
          <Route path="listings/:id" element={<ListingDetailPage />} />
          <Route
            path="listings/:id/compatible"
            element={<CompatibleSwapsPage />}
          />
          <Route path="my-listings" element={<MyListingsPage />} />
          <Route path="matches" element={<MatchesPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
