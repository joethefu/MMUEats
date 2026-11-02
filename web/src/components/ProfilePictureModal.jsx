import { useCallback, useEffect, useRef, useState } from "react";
import Cropper from "react-easy-crop";
import toast from "react-hot-toast";
import { FaCamera, FaTrash } from "react-icons/fa";
import { userService } from "../services/userService";
import { getCroppedBlob } from "../utils/cropImage";
import Avatar from "./Avatar";

const MAX_BYTES = 5 * 1024 * 1024;

/**
 * Click-the-avatar flow: choose a photo -> crop to a 1:1 square with live preview -> save,
 * or remove the current photo. Uploads as multipart/form-data via userService.
 */
export default function ProfilePictureModal({ open, user, onClose, onUpdated }) {
  const fileRef = useRef(null);
  const [src, setSrc] = useState(null);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [area, setArea] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);

  const reset = useCallback(() => {
    setSrc(null); setCrop({ x: 0, y: 0 }); setZoom(1); setArea(null); setPreview(null);
  }, []);

  useEffect(() => { if (!open) reset(); }, [open, reset]);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === "Escape" && !busy && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  // Keep a small live preview of exactly what will be saved.
  useEffect(() => {
    if (!src || !area) return undefined;
    let cancelled = false;
    const t = setTimeout(async () => {
      try {
        const blob = await getCroppedBlob(src, area, 160);
        if (!cancelled) setPreview((old) => { if (old) URL.revokeObjectURL(old); return URL.createObjectURL(blob); });
      } catch { /* preview is best-effort */ }
    }, 120);
    return () => { cancelled = true; clearTimeout(t); };
  }, [src, area]);

  if (!open) return null;

  const onFile = (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (!file.type.startsWith("image/")) return toast.error("Please choose an image file (JPG, PNG or WebP).");
    if (file.size > MAX_BYTES) return toast.error("That image is larger than 5 MB.");
    const reader = new FileReader();
    reader.onload = () => setSrc(reader.result);
    reader.readAsDataURL(file);
  };

  const save = async () => {
    setBusy(true);
    try {
      const blob = await getCroppedBlob(src, area, 512);
      const updated = await userService.uploadProfilePicture(blob, "avatar.jpg");
      toast.success("Profile picture updated");
      onUpdated(updated);
      onClose();
    } catch (err) {
      const e = err?.response?.data?.error;
      const details = e?.details && typeof e.details === "object" ? Object.values(e.details).flat().join(" ") : "";
      toast.error(details || e?.message || "Couldn't upload your picture.");
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    try {
      const updated = await userService.deleteProfilePicture();
      toast.success("Profile picture removed");
      onUpdated(updated);
      onClose();
    } catch {
      toast.error("Couldn't remove your picture.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center bg-black/50 sm:items-center sm:px-4" onMouseDown={(e) => e.target === e.currentTarget && !busy && onClose()}>
      <div role="dialog" aria-modal="true" aria-label="Profile picture" className="w-full max-w-md rounded-t-2xl bg-white p-5 shadow-xl sm:rounded-2xl">
        <h2 className="text-lg font-semibold text-slate-900">Profile picture</h2>

        {!src ? (
          <div className="mt-5 flex flex-col items-center">
            <Avatar user={user} size={128} />
            <div className="mt-5 flex w-full flex-col gap-2 sm:flex-row">
              <button onClick={() => fileRef.current?.click()} disabled={busy} className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
                <FaCamera /> {user.profile_picture ? "Change photo" : "Upload photo"}
              </button>
              {user.profile_picture && (
                <button onClick={remove} disabled={busy} className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-red-200 px-4 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-60">
                  <FaTrash size={12} /> {busy ? "Removing…" : "Remove photo"}
                </button>
              )}
            </div>
            <button onClick={onClose} className="mt-3 text-sm text-slate-500 hover:text-slate-700">Close</button>
            <p className="mt-2 text-xs text-slate-400">JPG, PNG or WebP, up to 5 MB.</p>
          </div>
        ) : (
          <div className="mt-4">
            <div className="relative h-64 w-full overflow-hidden rounded-xl bg-slate-900 sm:h-72">
              <Cropper
                image={src}
                crop={crop}
                zoom={zoom}
                aspect={1}
                cropShape="round"
                showGrid={false}
                onCropChange={setCrop}
                onZoomChange={setZoom}
                onCropComplete={(_, px) => setArea(px)}
              />
            </div>
            <div className="mt-4 flex items-center gap-4">
              <label className="flex flex-1 items-center gap-3 text-xs text-slate-500">
                Zoom
                <input type="range" min={1} max={3} step={0.05} value={zoom} onChange={(e) => setZoom(Number(e.target.value))} className="flex-1 accent-brand-600" aria-label="Zoom" />
              </label>
              <div className="text-center">
                <div className="h-14 w-14 overflow-hidden rounded-full bg-slate-100">{preview && <img src={preview} alt="Preview" className="h-full w-full object-cover" />}</div>
                <span className="text-[10px] text-slate-400">Preview</span>
              </div>
            </div>
            <div className="mt-5 flex gap-3">
              <button onClick={reset} disabled={busy} className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">Back</button>
              <button onClick={save} disabled={busy || !area} className="flex-1 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
                {busy ? "Saving…" : "Save picture"}
              </button>
            </div>
          </div>
        )}
        <input ref={fileRef} type="file" accept="image/*" onChange={onFile} className="hidden" />
      </div>
    </div>
  );
}
