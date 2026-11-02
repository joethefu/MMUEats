import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import { useAuth } from "../contexts/AuthContext";

export default function PublicLayout() {
  const { user } = useAuth();
  // Signed-in users get a fixed bottom tab bar on mobile, so leave room for it.
  return (
    <div className={`flex min-h-screen flex-col ${user ? "pb-16 md:pb-0" : ""}`}>
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
