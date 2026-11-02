import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/AuthContext";
import { useCart } from "../contexts/CartContext";

/** Shared "set this meal's quantity in my cart" logic (auth checks + friendly errors). */
export function useMealCart() {
  const { user } = useAuth();
  const { cart, addItem, removeItem } = useCart();
  const navigate = useNavigate();

  const itemFor = (mealId) => (cart?.items || []).find((i) => i.meal === mealId) || null;
  const quantityOf = (mealId) => itemFor(mealId)?.quantity || 0;

  const setQuantity = async (meal, quantity, specialInstructions = "") => {
    if (!user) {
      toast.error("Please log in to order.");
      navigate("/login");
      return false;
    }
    if (user.role !== "customer") {
      toast.error("Only customer accounts can order food.");
      return false;
    }
    try {
      if (quantity <= 0) {
        const existing = itemFor(meal.id);
        if (existing) await removeItem(existing.id);
      } else {
        await addItem(meal, quantity, specialInstructions);
      }
      return true;
    } catch (err) {
      const e = err?.response?.data?.error;
      if (e?.code === "different_restaurant") {
        toast.error(
          (t) => (
            <span>
              {e.message}{" "}
              <button className="ml-2 font-semibold underline" onClick={() => { navigate("/cart"); toast.dismiss(t.id); }}>
                Go to cart
              </button>
            </span>
          ),
          { duration: 6000 }
        );
      } else {
        toast.error(e?.message || e?.details?.meal_id?.[0] || "Couldn't update your cart.");
      }
      return false;
    }
  };

  return { quantityOf, itemFor, setQuantity };
}
