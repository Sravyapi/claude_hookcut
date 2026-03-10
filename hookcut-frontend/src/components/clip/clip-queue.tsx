"use client";

import { memo, useMemo, useCallback } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { formatClipTime } from "@/lib/clip-utils";

type ClipEntry = {
  id: string;
  startTime: number;
  endTime: number;
};

type ClipQueueProps = {
  clips: ClipEntry[];
  onRemove: (id: string) => void;
  onEdit: (id: string) => void;
};

const ClipItem = memo(function ClipItem({
  clip,
  index,
  onRemove,
  onEdit,
}: {
  clip: ClipEntry;
  index: number;
  onRemove: () => void;
  onEdit: () => void;
}) {
  const duration = clip.endTime - clip.startTime;

  return (
    <div className="flex items-center gap-3 py-3 px-4 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
      <div className="w-7 h-7 rounded-full bg-violet-500/20 text-violet-300 flex items-center justify-center text-xs font-bold shrink-0">
        #{index + 1}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-white">
          {formatClipTime(clip.startTime)} &rarr; {formatClipTime(clip.endTime)}
        </div>
        <div className="text-xs text-white/40">{duration.toFixed(1)}s</div>
      </div>
      <button
        onClick={onEdit}
        className="p-1.5 rounded-lg hover:bg-white/10 text-white/40 hover:text-white/80 transition-colors"
        aria-label={`Edit clip ${index + 1}`}
      >
        <Pencil className="w-3.5 h-3.5" />
      </button>
      <button
        onClick={onRemove}
        className="p-1.5 rounded-lg hover:bg-red-500/10 text-white/40 hover:text-red-400 transition-colors"
        aria-label={`Remove clip ${index + 1}`}
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
});

const ClipItemWrapper = memo(function ClipItemWrapper({
  clip,
  index,
  onRemove,
  onEdit,
}: {
  clip: ClipEntry;
  index: number;
  onRemove: (id: string) => void;
  onEdit: (id: string) => void;
}) {
  const handleRemove = useCallback(() => onRemove(clip.id), [onRemove, clip.id]);
  const handleEdit = useCallback(() => onEdit(clip.id), [onEdit, clip.id]);

  return (
    <ClipItem clip={clip} index={index} onRemove={handleRemove} onEdit={handleEdit} />
  );
});

export function ClipQueue({ clips, onRemove, onEdit }: ClipQueueProps) {
  const totalDuration = useMemo(
    () => clips.reduce((sum, c) => sum + (c.endTime - c.startTime), 0),
    [clips]
  );

  const handleRemove = useCallback((id: string) => onRemove(id), [onRemove]);
  const handleEdit = useCallback((id: string) => onEdit(id), [onEdit]);

  if (clips.length === 0) {
    return (
      <div className="py-8 text-center text-white/30 text-sm">
        Set start and end points above, then click Add Clip
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {clips.map((clip, i) => (
        <ClipItemWrapper
          key={clip.id}
          clip={clip}
          index={i}
          onRemove={handleRemove}
          onEdit={handleEdit}
        />
      ))}
      <div className="text-right text-sm text-white/50 pt-2">
        Total: {formatClipTime(totalDuration)}
      </div>
    </div>
  );
}
