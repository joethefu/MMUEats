import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";

import { AuthProvider } from "./contexts/AuthContext";
import { CartProvider } from "./contexts/CartContext";
import { NotificationProvider } from "./contexts/NotificationContext";
import ProtectedRoute from "./components/ProtectedRoute";
import PublicLayout from "./layouts/PublicLayout";
import VendorLayout from "./layouts/VendorLayout";

import HomePage from "./pages/HomePage";
import SignUpPage from "./pages/SignUpPage";
import LoginPage from "./pages/LoginPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import ResendVerificationPage from "./pages/ResendVerificationPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import BecomeVendorPage from "./pages/BecomeVendorPage";
import BecomeDeliveryPartnerPage from "./pages/BecomeDeliveryPartnerPage";
import RestaurantsPage from "./pages/RestaurantsPage";
import RestaurantDetailPage from "./pages/RestaurantDetailPage";
import CartPage from "./pages/CartPage";
import CheckoutPage from "./pages/CheckoutPage";
import OrdersPage from "./pages/OrdersPage";
import CustomerDashboardPage from "./pages/CustomerDashboardPage";
import ProfilePage from "./pages/ProfilePage";
import MealDetailPage from "./pages/MealDetailPage";
import OrderDetailPage from "./pages/OrderDetailPage";
import FavoritesPage from "./pages/FavoritesPage";
import VendorDashboardPage from "./pages/vendor/VendorDashboardPage";
import VendorRestaurantProfilePage from "./pages/vendor/VendorRestaurantProfilePage";
import VendorMenuPage from "./pages/vendor/VendorMenuPage";
import VendorOrdersPage from "./pages/vendor/VendorOrdersPage";
import VendorReportsPage from "./pages/vendor/VendorReportsPage";
import StartupAdPopup from "./components/StartupAdPopup";
import DeliveryLayout from "./layouts/DeliveryLayout";
import DeliveryDashboardPage from "./pages/delivery/DeliveryDashboardPage";
import AvailableDeliveriesPage from "./pages/delivery/AvailableDeliveriesPage";
import CurrentDeliveryPage from "./pages/delivery/CurrentDeliveryPage";
import DeliveryHistoryPage from "./pages/delivery/DeliveryHistoryPage";
import EarningsPage from "./pages/delivery/EarningsPage";
import AdminLayout from "./layouts/AdminLayout";
import AdminAdvertisementsPage from "./pages/admin/AdminAdvertisementsPage";
import AdminDashboardPage from "./pages/admin/AdminDashboardPage";
import AdminUsersPage from "./pages/admin/AdminUsersPage";
import AdminApplicationsPage from "./pages/admin/AdminApplicationsPage";
import { AboutPage, ContactPage, HelpPage, TermsPage, PrivacyPage, NotFoundPage } from "./pages/StaticPages";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <CartProvider>
          <NotificationProvider>
          <Toaster position="top-right" />
          <StartupAdPopup />
          <Routes>
            <Route element={<PublicLayout />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />
              <Route path="/resend-verification" element={<ResendVerificationPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="/become-a-vendor" element={<BecomeVendorPage />} />
              <Route path="/become-a-delivery-partner" element={<BecomeDeliveryPartnerPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/contact" element={<ContactPage />} />
              <Route path="/help" element={<HelpPage />} />
              <Route path="/terms" element={<TermsPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/restaurants" element={<RestaurantsPage />} />
              <Route path="/restaurants/:slug" element={<RestaurantDetailPage />} />
              <Route path="/meals/:id" element={<MealDetailPage />} />

              <Route element={<ProtectedRoute />}>
                <Route path="/profile" element={<ProfilePage />} />
              </Route>

              <Route element={<ProtectedRoute allowedRoles={["customer"]} />}>
                <Route path="/dashboard" element={<CustomerDashboardPage />} />
                <Route path="/cart" element={<CartPage />} />
                <Route path="/checkout" element={<CheckoutPage />} />
                <Route path="/orders" element={<OrdersPage />} />
                <Route path="/orders/:id" element={<OrderDetailPage />} />
                <Route path="/favorites" element={<FavoritesPage />} />
              </Route>

              <Route path="*" element={<NotFoundPage />} />
            </Route>

            <Route element={<ProtectedRoute allowedRoles={["vendor"]} />}>
              <Route element={<VendorLayout />}>
                <Route path="/vendor/dashboard" element={<VendorDashboardPage />} />
                <Route path="/vendor/restaurant" element={<VendorRestaurantProfilePage />} />
                <Route path="/vendor/menu" element={<VendorMenuPage />} />
                <Route path="/vendor/orders" element={<VendorOrdersPage />} />
                <Route path="/vendor/reports" element={<VendorReportsPage />} />
              </Route>
            </Route>

            <Route element={<ProtectedRoute allowedRoles={["delivery_partner"]} />}>
              <Route element={<DeliveryLayout />}>
                <Route path="/delivery/dashboard" element={<DeliveryDashboardPage />} />
                <Route path="/delivery/available" element={<AvailableDeliveriesPage />} />
                <Route path="/delivery/current" element={<CurrentDeliveryPage />} />
                <Route path="/delivery/history" element={<DeliveryHistoryPage />} />
                <Route path="/delivery/earnings" element={<EarningsPage />} />
              </Route>
            </Route>

            <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
              <Route element={<AdminLayout />}>
                <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
                <Route path="/admin/applications" element={<AdminApplicationsPage />} />
                <Route path="/admin/users" element={<AdminUsersPage />} />
                <Route path="/admin/advertisements" element={<AdminAdvertisementsPage />} />
              </Route>
            </Route>
          </Routes>
          </NotificationProvider>
          </CartProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
