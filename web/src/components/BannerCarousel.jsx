import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { advertisementService } from "../services/advertisementService";

const INTERVAL_MS = 3000;
const SLIDE_COUNT = 3;
const SWIPE_PX = 45;

// Branded fallbacks so the banner always has exactly three slides, even before admins add promotions.
const DEFAULT_SLIDES = [
  { key: "d1", title: "Hungry? We deliver to your hostel", description: "Order from MMU's favourite vendors in a few taps.", cta_label: "Order now", link: "/restaurants", tone: "from-brand-700 to-brand-500" },
  { key: "d2", title: "Fresh deals every day", description: "Discounted meals from campus kitchens.", cta_label: "See menu", link: "/restaurants", tone: "from-gold-500 to-brand-600" },
  { key: "d3", title: "Sell on MMUEats", description: "Run a campus kitchen? Reach thousands of hungry students.", cta_label: "Become a vendor", link: "/become-a-vendor", tone: "from-slate-800 to-brand-700" },
];

const isExternal = (url) => /^https?:\/\//i.test(url || "");

function SlideBody({ slide }) {
  const hasText = slide.title || slide.description || slide.cta_label;
  return (
    <>
      {slide.image ? (
        <img src={slide.image} alt={slide.title || "Promotion"} draggable={false} className="absolute inset-0 h-full w-full object-cover" />
      ) : (
        <div className={`absolute inset-0 bg-gradient-to-r ${slide.tone || "from-brand-700 to-brand-500"}`} />
      )}
      {hasText && (
        <>
          {slide.image && <div className="absolute inset-0 bg-gradient-to-r from-black/65 via-black/30 to-transparent" />}
          <div className="relative flex h-full max-w-xl flex-col justify-center gap-2 px-6 py-4 text-white sm:px-10">
            {slide.title && <h2 className="text-xl font-extrabold leading-tight sm:text-3xl">{slide.title}</h2>}
            {slide.description && <p className="line-clamp-2 text-sm text-white/90 sm:text-base">{slide.description}</p>}
            {slide.cta_label && (
              <span className="mt-1 inline-block w-fit rounded-lg bg-white px-4 py-2 text-sm font-semibold text-brand-700 shadow">
                {slide.cta_label}
              </span>
            )}
          </div>
        </>
      )}
    </>
  );
}

export default function BannerCarousel() {
  const [slides, setSlides] = useState(DEFAULT_SLIDES);
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const drag = useRef({ x: null, moved: false });
  const seen = useRef(new Set());

  useEffect(() => {
    advertisementService
      .getActive("homepage_banner")
      .then((ads) => {
        const fromAds = (ads || []).slice(0, SLIDE_COUNT).map((ad) => ({
          key: ad.id, adId: ad.id, image: ad.image, title: ad.title, description: ad.description,
          cta_label: ad.cta_label, link: ad.external_url,
        }));
        setSlides([...fromAds, ...DEFAULT_SLIDES].slice(0, SLIDE_COUNT));
      })
      .catch(() => {});
  }, []);

  const go = useCallback((i) => setIndex((i + SLIDE_COUNT) % SLIDE_COUNT), []);

  // Auto-rotate every 3 s; pause while hovering/touching so swipes aren't fought by the timer.
  useEffect(() => {
    if (paused) return undefined;
    const t = setTimeout(() => go(index + 1), INTERVAL_MS);
    return () => clearTimeout(t);
  }, [index, paused, go]);

  // Count one impression per real promotion the first time it is shown.
  useEffect(() => {
    const s = slides[index];
    if (s?.adId && !seen.current.has(s.adId)) {
      seen.current.add(s.adId);
      advertisementService.trackImpression(s.adId).catch(() => {});
    }
  }, [index, slides]);

  const onPointerDown = (e) => {
    drag.current = { x: e.clientX, moved: false };
    setPaused(true);
  };
  const onPointerUp = (e) => {
    const { x } = drag.current;
    if (x != null) {
      const dx = e.clientX - x;
      if (Math.abs(dx) > SWIPE_PX) {
        drag.current.moved = true;
        go(index + (dx < 0 ? 1 : -1));
      }
    }
    drag.current.x = null;
    if (e.pointerType !== "mouse") setPaused(false);
  };

  const handleClick = (e, slide) => {
    if (drag.current.moved) {
      e.preventDefault(); // it was a swipe, not a tap
      drag.current.moved = false;
      return;
    }
    if (slide.adId) advertisementService.trackClick(slide.adId).catch(() => {});
  };

  const renderSlide = (slide, i) => {
    const common = {
      "aria-hidden": i !== index,
      tabIndex: i === index ? 0 : -1,
      onClick: (e) => handleClick(e, slide),
      className: "relative block h-full w-full shrink-0 basis-full overflow-hidden",
    };
    if (!slide.link) return <div key={slide.key} {...common}><SlideBody slide={slide} /></div>;
    return isExternal(slide.link) ? (
      <a key={slide.key} {...common} href={slide.link} target="_blank" rel="noopener noreferrer" draggable={false}><SlideBody slide={slide} /></a>
    ) : (
      <Link key={slide.key} {...common} to={slide.link} draggable={false}><SlideBody slide={slide} /></Link>
    );
  };

  return (
    <section aria-roledescription="carousel" aria-label="Promotions" className="mx-auto w-full max-w-7xl px-0 sm:px-6 sm:pt-4 lg:px-8">
      <div
        className="relative overflow-hidden bg-slate-100 sm:rounded-2xl"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
        onPointerDown={onPointerDown}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        style={{ touchAction: "pan-y" }}
      >
        <div
          data-testid="banner-track"
          className="flex h-40 transition-transform duration-500 ease-out motion-reduce:transition-none sm:h-56 lg:h-72"
          style={{ transform: `translateX(-${index * 100}%)` }}
        >
          {slides.map(renderSlide)}
        </div>

        <div className="absolute inset-x-0 bottom-2 flex justify-center gap-2">
          {slides.map((s, i) => (
            <button
              key={s.key}
              type="button"
              aria-label={`Go to slide ${i + 1}`}
              aria-current={i === index}
              onClick={(e) => { e.stopPropagation(); go(i); }}
              className={`h-2 rounded-full transition-all ${i === index ? "w-6 bg-white" : "w-2 bg-white/60 hover:bg-white/90"}`}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
