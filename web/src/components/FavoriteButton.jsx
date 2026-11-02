import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { FaHeart, FaRegHeart } from "react-icons/fa";
import { useAuth } from "../contexts/AuthContext";

/**
 * Heart toggle. `api` = { add(id) -> {id}, remove(favoriteId) }.
 * Keeps its own optimistic state, seeded from the item's is_favorited / favorite_id.
 */
export default function FavoriteButton({ itemId, isFavorited, favoriteId, api, className = "", size = 18, onChange }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [fav, setFav] = useState({ on: !!isFavorited, id: favoriteId || null });
  const [busy, setBusy] = useState(false);

  useEffect(() => setFav({ on: !!isFavorited, id: favoriteId || null }), [isFavorited, favoriteId]);

  const toggle = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!user) {
      toast.error("Log in to save favorites.");
      navigate("/login");
      return;
    }
    if (user.role !== "customer") return toast.error("Only customers can save favorites.");
    if (busy) return;
    setBusy(true);
    const previous = fav;
    try {
      if (fav.on) {
        setFav({ on: false, id: null });
        await api.remove(fav.id);
        onChange?.(false, null);
      } else {
        setFav({ on: true, id: null });
        const created = await api.add(itemId);
        setFav({ on: true, id: created.id });
        onChange?.(true, created.id);
      }
    } catch {
      setFav(previous);
      toast.error("Couldn't update your favorites.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={fav.on}
      aria-label={fav.on ? "Remove from favorites" : "Add to favorites"}
      className={`flex items-center justify-center rounded-full bg-white/90 p-2 text-brand-600 shadow-sm hover:bg-white ${className}`}
    >
      {fav.on ? <FaHeart size={size} /> : <FaRegHeart size={size} />}
    </button>
  );
}
