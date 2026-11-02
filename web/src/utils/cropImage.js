/** Crop `imageSrc` to the pixel area from react-easy-crop and return a square JPEG Blob. */
export async function getCroppedBlob(imageSrc, area, outputSize = 512) {
  const img = await new Promise((resolve, reject) => {
    const i = new Image();
    i.onload = () => resolve(i);
    i.onerror = reject;
    i.src = imageSrc;
  });
  const canvas = document.createElement("canvas");
  canvas.width = outputSize;
  canvas.height = outputSize;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(img, area.x, area.y, area.width, area.height, 0, 0, outputSize, outputSize);
  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("Could not process the image."))), "image/jpeg", 0.9)
  );
}
