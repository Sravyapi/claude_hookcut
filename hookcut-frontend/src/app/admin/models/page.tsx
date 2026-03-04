"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Cpu,
  Eye,
  EyeOff,
  Save,
  Star,
  ToggleLeft,
  ToggleRight,
  Key,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import type { ProviderConfig } from "@/lib/types";
import { useToast } from "@/components/ui/use-toast";
import { staggerContainer, fadeUpItem } from "@/lib/motion";

/* ─── Constants ─── */

const DEFAULT_MODELS: Record<string, string> = {
  gemini: "gemini-2.5-flash",
  anthropic: "claude-sonnet-4-20250514",
  openai: "gpt-4o",
};

const PROVIDER_COLORS: Record<string, { accent: string; border: string; bg: string }> = {
  gemini: {
    accent: "text-blue-300",
    border: "border-blue-500/20",
    bg: "bg-blue-500/10",
  },
  anthropic: {
    accent: "text-amber-300",
    border: "border-amber-500/20",
    bg: "bg-amber-500/10",
  },
  openai: {
    accent: "text-emerald-300",
    border: "border-emerald-500/20",
    bg: "bg-emerald-500/10",
  },
};

function getProviderColor(name: string) {
  return (
    PROVIDER_COLORS[name.toLowerCase()] || {
      accent: "text-violet-300",
      border: "border-violet-500/20",
      bg: "bg-violet-500/10",
    }
  );
}

/* ─── Provider Card ─── */

function ProviderCard({
  provider,
  onRefresh,
}: {
  provider: ProviderConfig;
  onRefresh: () => void;
}) {
  const { toast } = useToast();
  const [modelId, setModelId] = useState(provider.model_id || DEFAULT_MODELS[provider.provider_name.toLowerCase()] || "");
  const [enabled, setEnabled] = useState(provider.is_enabled);
  const [saving, setSaving] = useState(false);
  const [settingPrimary, setSettingPrimary] = useState(false);

  // API Key section
  const [showKeyInput, setShowKeyInput] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [updatingKey, setUpdatingKey] = useState(false);

  const colors = getProviderColor(provider.provider_name);

  // Sync local state when provider prop changes
  useEffect(() => {
    setModelId(provider.model_id || DEFAULT_MODELS[provider.provider_name.toLowerCase()] || "");
    setEnabled(provider.is_enabled);
  }, [provider]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.adminUpdateProvider(provider.provider_name, {
        is_enabled: enabled,
        model_id: modelId,
      });
      onRefresh();
    } catch (err) {
      console.warn("Failed to update provider:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleSetPrimary = async () => {
    setSettingPrimary(true);
    try {
      await api.adminSetPrimary(provider.provider_name);
      onRefresh();
    } catch (err) {
      console.warn("Failed to set primary:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setSettingPrimary(false);
    }
  };

  const handleUpdateKey = async () => {
    if (!apiKey.trim()) return;
    setUpdatingKey(true);
    try {
      await api.adminSetApiKey(provider.provider_name, apiKey);
      setApiKey("");
      setShowKeyInput(false);
      onRefresh();
    } catch (err) {
      console.warn("Failed to update API key:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setUpdatingKey(false);
    }
  };

  const displayName =
    provider.provider_name.charAt(0).toUpperCase() +
    provider.provider_name.slice(1);

  return (
    <motion.div
      variants={fadeUpItem}
      className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-xl ${colors.bg} flex items-center justify-center`}
          >
            <Cpu className={`w-5 h-5 ${colors.accent}`} />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">
              {displayName}
            </h3>
          </div>
        </div>
        {/* Role badges */}
        <div className="flex items-center gap-1.5">
          {provider.is_primary && (
            <span className="text-[10px] px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/25 font-medium">
              Primary
            </span>
          )}
          {provider.is_fallback && (
            <span className="text-[10px] px-2.5 py-1 rounded-full bg-blue-500/15 text-blue-300 border border-blue-500/25 font-medium">
              Fallback
            </span>
          )}
        </div>
      </div>

      {/* Model ID */}
      <div className="mb-4">
        <label className="text-xs font-medium text-white/40 mb-2 block">
          Model ID
        </label>
        <input
          type="text"
          value={modelId}
          onChange={(e) => setModelId(e.target.value)}
          placeholder={DEFAULT_MODELS[provider.provider_name.toLowerCase()] || "model-id"}
          className="w-full px-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm text-white/80 placeholder-white/20 outline-none focus:border-violet-500/40 focus:ring-1 focus:ring-violet-500/20 transition-all font-mono"
        />
      </div>

      {/* API Key Status */}
      <div className="mb-4">
        <label className="text-xs font-medium text-white/40 mb-2 block">
          API Key Status
        </label>
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          {provider.api_key_set ? (
            <>
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="text-sm text-white/60 font-mono">
                ****{provider.api_key_last4}
              </span>
            </>
          ) : (
            <>
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span className="text-sm text-white/40">Not configured</span>
            </>
          )}
        </div>
      </div>

      {/* Enabled toggle */}
      <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] mb-4">
        <span className="text-sm text-white/60">Enabled</span>
        <button
          onClick={() => setEnabled(!enabled)}
          className="flex items-center gap-2 text-sm"
        >
          {enabled ? (
            <>
              <ToggleRight className="w-6 h-6 text-emerald-400" />
              <span className="text-emerald-300">On</span>
            </>
          ) : (
            <>
              <ToggleLeft className="w-6 h-6 text-white/30" />
              <span className="text-white/40">Off</span>
            </>
          )}
        </button>
      </div>

      {/* Set as Primary */}
      {!provider.is_primary && (
        <button
          onClick={handleSetPrimary}
          disabled={settingPrimary}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-white/[0.08] text-white/50 hover:text-white/70 hover:bg-white/[0.03] transition-all duration-200 text-sm mb-4 disabled:opacity-50"
        >
          <Star className="w-4 h-4" />
          {settingPrimary ? "Setting..." : "Set as Primary"}
        </button>
      )}

      {/* Update API Key */}
      <div className="mb-4">
        {!showKeyInput ? (
          <button
            onClick={() => setShowKeyInput(true)}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-dashed border-white/10 text-white/40 hover:text-white/60 hover:border-white/20 hover:bg-white/[0.02] transition-all duration-200 text-sm"
          >
            <Key className="w-4 h-4" />
            Update API Key
          </button>
        ) : (
          <div className="space-y-2">
            <div className="relative">
              <input
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Paste new API key..."
                className="w-full px-4 py-2.5 pr-10 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm text-white/80 placeholder-white/20 outline-none focus:border-violet-500/40 focus:ring-1 focus:ring-violet-500/20 transition-all font-mono"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/50 transition-colors"
              >
                {showKey ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleUpdateKey}
                disabled={updatingKey || !apiKey.trim()}
                className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl bg-violet-500/15 text-violet-300 border border-violet-500/30 hover:bg-violet-500/25 transition-all duration-200 text-sm font-medium disabled:opacity-50"
              >
                <Key className="w-3.5 h-3.5" />
                {updatingKey ? "Updating..." : "Update Key"}
              </button>
              <button
                onClick={() => {
                  setShowKeyInput(false);
                  setApiKey("");
                  setShowKey(false);
                }}
                className="px-4 py-2 rounded-xl text-sm text-white/40 hover:text-white/60 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Save button */}
      <div className="mt-auto pt-2">
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-violet-500/15 text-violet-300 border border-violet-500/30 hover:bg-violet-500/25 transition-all duration-200 text-sm font-medium disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          {saving ? "Saving..." : "Save"}
        </button>
      </div>
    </motion.div>
  );
}

/* ─── Main Page ─── */

export default function ModelProviderPage() {
  const { toast } = useToast();
  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchProviders = useCallback(async () => {
    try {
      const data = await api.adminProviders();
      setProviders(data.providers);
    } catch (err) {
      console.warn("Failed to load providers:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  return (
    <div className="space-y-6">
        {/* Header */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Cpu className="w-6 h-6 text-violet-400" />
            Model / Provider Management
          </h1>
          <p className="text-white/40 text-sm mt-0.5">
            Configure LLM providers, API keys, and model selection
          </p>
        </motion.div>

        {/* Provider cards grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="h-96 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl animate-pulse"
              />
            ))}
          </div>
        ) : providers.length > 0 ? (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            {providers.map((provider) => (
              <ProviderCard
                key={provider.provider_name}
                provider={provider}
                onRefresh={fetchProviders}
              />
            ))}
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-12 text-center"
          >
            <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/[0.05] flex items-center justify-center mx-auto mb-4">
              <Cpu className="w-7 h-7 text-white/15" />
            </div>
            <p className="text-white/40 text-sm mb-1">
              No providers configured
            </p>
            <p className="text-white/25 text-xs">
              Provider configurations will appear here once the backend is set up
            </p>
          </motion.div>
        )}
    </div>
  );
}
