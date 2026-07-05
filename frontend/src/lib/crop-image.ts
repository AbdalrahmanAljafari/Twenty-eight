export const FACE_INPUT_SIZE = 512;
export const FACE_CROP_BACKGROUND = "#FFFFFF";

export interface CropArea {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface MediaSize {
  width: number;
  height: number;
  naturalWidth: number;
  naturalHeight: number;
}

export interface FaceCropExportParams {
  imageSrc: string;
  crop: { x: number; y: number };
  zoom: number;
  mediaSize: MediaSize;
  cropSize: { width: number; height: number };
  outputSize?: number;
  backgroundColor?: string;
  fileName?: string;
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.addEventListener("load", () => resolve(image));
    image.addEventListener("error", () => reject(new Error("Failed to load image")));
    image.src = src;
  });
}

/** Fit zoom: entire image visible inside the crop box at this zoom level. */
export function getFitZoom(
  mediaSize: Pick<MediaSize, "width" | "height">,
  cropSize: { width: number; height: number },
): number {
  return Math.min(cropSize.width / mediaSize.width, cropSize.height / mediaSize.height);
}

/**
 * Export the crop viewport to a square image.
 * Areas outside the source image are filled with white (letterbox).
 */
export async function exportFaceCropToFile({
  imageSrc,
  crop,
  zoom,
  mediaSize,
  cropSize,
  outputSize = FACE_INPUT_SIZE,
  backgroundColor = FACE_CROP_BACKGROUND,
  fileName = "face.jpg",
}: FaceCropExportParams): Promise<File> {
  const image = await loadImage(imageSrc);
  const canvas = document.createElement("canvas");
  canvas.width = outputSize;
  canvas.height = outputSize;

  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Could not get canvas context");

  ctx.fillStyle = backgroundColor;
  ctx.fillRect(0, 0, outputSize, outputSize);

  const scale = outputSize / cropSize.width;
  const displayWidth = mediaSize.width * zoom;
  const displayHeight = mediaSize.height * zoom;

  const destX = (cropSize.width / 2 + crop.x - displayWidth / 2) * scale;
  const destY = (cropSize.height / 2 + crop.y - displayHeight / 2) * scale;
  const destW = displayWidth * scale;
  const destH = displayHeight * scale;

  ctx.drawImage(
    image,
    0,
    0,
    mediaSize.naturalWidth,
    mediaSize.naturalHeight,
    destX,
    destY,
    destW,
    destH,
  );

  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (result) => {
        if (result) resolve(result);
        else reject(new Error("Crop failed"));
      },
      "image/jpeg",
      0.92,
    );
  });

  return new File([blob], fileName, { type: "image/jpeg" });
}
