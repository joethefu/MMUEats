/** Circular avatar: profile picture if set, otherwise the user's initials. */
export default function Avatar({ user, size = 32, className = "" }) {
  const initials = (user?.full_name || user?.email || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");
  const style = { width: size, height: size, fontSize: Math.max(11, size * 0.38) };
  return user?.profile_picture ? (
    <img src={user.profile_picture} alt={user.full_name || "Profile"} style={style} className={`rounded-full object-cover ${className}`} />
  ) : (
    <span style={style} className={`flex items-center justify-center rounded-full bg-brand-600 font-semibold text-white ${className}`}>
      {initials}
    </span>
  );
}
