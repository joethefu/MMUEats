import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { FaTrash } from "react-icons/fa";
import { useCart } from "../contexts/CartContext";
import QuantityStepper from "../components/QuantityStepper";

export default function CartPage() {
  const { cart, addItem, removeItem, clearCart, isLoading } = useCart();
  const navigate = useNavigate();

  if (isLoading) return <div className="mx-auto max-w-3xl px-4 py-16 text-slate-500">Loading cart…</div>;

  const items = cart?.items || [];

  if (items.length === 0) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center px-4 py-24 text-center">
        <h1 className="text-2xl font-bold text-slate-900">Your cart is empty</h1>
        <p className="mt-2 text-slate-600">Browse restaurants and add something tasty.</p>
        <Link to="/restaurants" className="mt-6 rounded-lg bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
          Browse Restaurants
        </Link>
      </div>
    );
  }

  const handleQuantity = async (item, quantity) => {
    try {
      await addItem({ id: item.meal }, quantity, item.special_instructions);
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || "Couldn't change the quantity.");
    }
  };

  const handleRemove = async (itemId) => {
    try {
      await removeItem(itemId);
    } catch {
      toast.error("Couldn't remove that item.");
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-bold text-slate-900">Your Cart</h1>
      <p className="mt-1 text-sm text-slate-500">Ordering from {cart.restaurant_name}</p>

      <div className="mt-6 divide-y divide-slate-200 rounded-xl border border-slate-200">
        {items.map((item) => (
          <div key={item.id} className="flex items-center gap-3 p-3 sm:gap-4 sm:p-4">
            <div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg bg-slate-100 sm:h-20 sm:w-20">
              {item.meal_image ? (
                <img src={item.meal_image} alt={item.meal_name} className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-2xl font-bold text-brand-200">{item.meal_name[0]}</div>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <Link to={`/meals/${item.meal}`} className="block truncate font-medium text-slate-900 hover:text-brand-600">{item.meal_name}</Link>
              {item.special_instructions && <p className="truncate text-xs text-slate-500">Note: {item.special_instructions}</p>}
              <p className="mt-0.5 text-xs text-slate-500">
                KES {item.unit_price}{Number(item.packaging_fee) > 0 && ` + KES ${item.packaging_fee} container`} each
              </p>
              <div className="mt-2 flex items-center justify-between">
                <QuantityStepper size="sm" value={item.quantity} onChange={(n) => handleQuantity(item, n)} />
                <span className="text-sm font-semibold text-slate-900">KES {item.line_total}</span>
              </div>
            </div>
            <button onClick={() => handleRemove(item.id)} aria-label={`Remove ${item.meal_name}`} className="self-start p-1 text-slate-400 hover:text-red-600">
              <FaTrash />
            </button>
          </div>
        ))}
      </div>

      {Number(cart.packaging_total) > 0 && (
        <p className="mt-4 text-right text-xs text-slate-500">Container charges included: KES {cart.packaging_total}</p>
      )}
      <div className="mt-2 flex items-center justify-between border-t border-slate-200 pt-4">
        <span className="font-medium text-slate-700">Subtotal</span>
        <span className="font-bold text-slate-900">KES {cart.subtotal}</span>
      </div>

      <div className="mt-6 flex gap-3">
        <button
          onClick={() => clearCart().catch(() => toast.error("Couldn't clear the cart."))}
          className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Clear Cart
        </button>
        <button
          onClick={() => navigate("/checkout")}
          className="flex-1 rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
        >
          Proceed to Checkout
        </button>
      </div>
    </div>
  );
}
