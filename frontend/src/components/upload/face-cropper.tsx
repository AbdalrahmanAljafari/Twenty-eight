"use client";

import { useCallback, useState } from "react";
import Cropper, { type MediaSize } from "react-easy-crop";
import "react-easy-crop/react-easy-crop.css";

import { Button } from "@/components/ui/button";
import { copy } from "@/lib/copy";
import {
  exportFaceCropToFile,
  FACE_CROP_BACKGROUND,
  getFitZoom,
} from "@/lib/crop-image";

const CROP_BOX_SIZE = 280;

interface FaceCropperProps {
  imageSrc: string;
  onCropComplete: (file: File, previewUrl: string) => void;
  onCancel: () => void;
}

export function FaceCropper({ imageSrc, onCropComplete, onCancel }: FaceCropperProps) {
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [minZoom, setMinZoom] = useState(0.1);
  const [mediaSize, setMediaSize] = useState<MediaSize | null>(null);
  const [cropSize, setCropSize] = useState({ width: CROP_BOX_SIZE, height: CROP_BOX_SIZE });
  const [isApplying, setIsApplying] = useState(false);

  const handleMediaLoaded = useCallback((size: MediaSize) => {
    setMediaSize(size);

    const fitZoom = getFitZoom(size, { width: CROP_BOX_SIZE, height: CROP_BOX_SIZE });
    const computedMinZoom = Math.max(0.1, fitZoom * 0.4);

    setMinZoom(computedMinZoom);
    setZoom(Math.min(1, fitZoom));
    setCrop({ x: 0, y: 0 });
  }, []);

  const handleApply = async () => {
    if (!mediaSize) return;

    setIsApplying(true);
    try {
      const file = await exportFaceCropToFile({
        imageSrc,
        crop,
        zoom,
        mediaSize,
        cropSize,
      });
      const previewUrl = URL.createObjectURL(file);
      onCropComplete(file, previewUrl);
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{copy.face.cropHint}</p>

      <div
        className="relative mx-auto aspect-square w-full max-w-[512px] overflow-hidden rounded-xl border border-primary/40"
        style={{ backgroundColor: FACE_CROP_BACKGROUND }}
      >
        <Cropper
          image={imageSrc}
          crop={crop}
          zoom={zoom}
          minZoom={minZoom}
          maxZoom={3}
          aspect={1}
          cropSize={cropSize}
          restrictPosition
          showGrid
          onCropChange={setCrop}
          onZoomChange={setZoom}
          onMediaLoaded={handleMediaLoaded}
          onCropSizeChange={setCropSize}
          objectFit="contain"
          style={{
            containerStyle: { backgroundColor: FACE_CROP_BACKGROUND },
            cropAreaStyle: { border: "2px solid #7c3aed" },
          }}
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm text-muted-foreground" htmlFor="face-crop-zoom">
          {copy.face.zoomLabel}
        </label>
        <input
          id="face-crop-zoom"
          type="range"
          min={minZoom}
          max={3}
          step={0.05}
          value={zoom}
          onChange={(event) => setZoom(Number(event.target.value))}
          className="w-full accent-primary"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isApplying}>
          {copy.face.back}
        </Button>
        <Button type="button" onClick={handleApply} disabled={!mediaSize || isApplying}>
          {isApplying ? copy.face.cropApplying : copy.face.cropApply}
        </Button>
      </div>
    </div>
  );
}
