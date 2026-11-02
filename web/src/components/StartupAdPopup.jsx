import { useEffect, useState } from "react";
import { FaTimes } from "react-icons/fa";
import { advertisementService } from "../services/advertisementService";

const LAST_SHOWN_KEY = "mmueats_ad_last_shown_date";

function todayStr() {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD, calendar-day granularity
}

export default function StartupAdPopup() {
  const [ad, setAd] = useState(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const lastShown = localStorage.getItem(LAST_SHOWN_KEY);
    if (lastShown === todayStr()) {
      return; // Already shown today — spec §43: only once per calendar day.
    }

    advertisementService
      .getActive("startup_popup")
      .then((ads) => {
        if (ads && ads.length > 0) {
          setAd(ads[0]); // highest priority active ad, per backend ordering
          setVisible(true);
          advertisementService.trackImpression(ads[0].id).catch(() => {});
          localStorage.setItem(LAST_SHOWN_KEY, todayStr());
        }
      })
      .catch(() => {
        // No active ad or request failed — fail silently, never block the app.
      });
  }, []);

  if (!visible || !ad) return null;

  const handleClick = async () => {
    const open = (url) => {
      if (!url) return;
      // Internal paths open inside the app; full URLs open in a new tab.
      if (url.startsWith("/")) window.location.assign(url);
      else window.open(url, "_blank", "noopener,noreferrer");
    };
    try {
      const result = await advertisementService.trackClick(ad.id);
      open(result.destination_url);
    } catch {
      open(ad.external_url);
    }
    setVisible(false);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4">
      <div className="relative max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl">
        <button
          onClick={() => setVisible(false)}
          aria-label="Close advertisement"
          className="absolute right-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-white/90 text-slate-700 shadow hover:bg-white"
        >
          <FaTimes />
        </button>
        <button onClick={handleClick} className="block w-full">
          <img src={ad.image} alt={ad.title} className="w-full object-cover" />
        </button>
      </div>
    </div>
  );
}
