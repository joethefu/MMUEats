import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { cartService } from "../services/orderService";
import { useAuth } from "./AuthContext";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const { user } = useAuth();
  const [cart, setCart] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const refreshCart = useCallback(async () => {
    if (!user || user.role !== "customer") {
      setCart(null);
      return;
    }
    setIsLoading(true);
    try {
      const data = await cartService.get();
      setCart(data);
    } catch {
      setCart(null);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  const addItem = async (meal, quantity = 1, specialInstructions = "") => {
    const data = await cartService.addItem({ meal_id: meal.id, quantity, special_instructions: specialInstructions });
    setCart(data);
    return data;
  };

  const removeItem = async (itemId) => {
    const data = await cartService.removeItem(itemId);
    setCart(data);
  };

  const clearCart = async () => {
    const data = await cartService.clear();
    setCart(data);
  };

  const itemCount = cart?.items?.reduce((sum, i) => sum + i.quantity, 0) || 0;

  return (
    <CartContext.Provider value={{ cart, isLoading, itemCount, refreshCart, addItem, removeItem, clearCart }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within a CartProvider");
  return ctx;
}
