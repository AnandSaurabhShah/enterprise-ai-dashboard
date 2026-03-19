import React, { useEffect, useMemo, useRef, useState } from "react";

import { assistiveLocales, describeAssistiveLocale, indianAssistiveLocales } from "../lib/assistive";
import { Badge, Button, Card, Select } from "./ui";

type TextField = {
  name: string;
  label: string;
  type: string;
};

type AssistiveControlsProps = {
  textFields: TextField[];
  targetField: string;
  onTargetFieldChange: (fieldName: string) => void;
  onInsertText: (text: string) => void;
  onClearTargetField: () => void;
  onSubmit: () => void;
  narrationText: string;
};

type SpeechRecognitionAlternativeLike = {
  transcript?: string;
};

type SpeechRecognitionResultLike = {
  isFinal?: boolean;
  0?: SpeechRecognitionAlternativeLike;
};

type SpeechRecognitionEventLike = {
  results: ArrayLike<SpeechRecognitionResultLike>;
};

type SpeechRecognitionErrorEventLike = {
  error?: string;
};

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  maxAlternatives: number;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

type BrowserSpeechWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

type GesturePoint = {
  pointerId: number;
  x: number;
  y: number;
  startedAt: number;
};

export function AssistiveControls({
  textFields,
  targetField,
  onTargetFieldChange,
  onInsertText,
  onClearTargetField,
  onSubmit,
  narrationText,
}: AssistiveControlsProps) {
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const gestureStartRef = useRef<GesturePoint | null>(null);
  const [selectedLocale, setSelectedLocale] = useState("hi-IN");
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Voice dictation and assistive gestures are ready.");
  const [transcriptPreview, setTranscriptPreview] = useState("");

  const recognitionConstructor = useMemo(() => {
    if (typeof window === "undefined") {
      return null;
    }

    const speechWindow = window as BrowserSpeechWindow;
    return speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition ?? null;
  }, []);

  const selectedLocaleDetails = describeAssistiveLocale(selectedLocale);
  const targetFieldLabel = textFields.find((field) => field.name === targetField)?.label || "No text field selected";

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const stopSpeechInput = () => {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setListening(false);
  };

  const stopNarration = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  };

  const startDictation = () => {
    if (!recognitionConstructor) {
      setStatusMessage("This browser does not expose speech recognition.");
      return;
    }

    if (!textFields.length || !targetField) {
      setStatusMessage("Select or focus a text field before starting dictation.");
      return;
    }

    stopSpeechInput();

    const recognition = new recognitionConstructor();
    recognition.lang = selectedLocale;
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      let preview = "";
      const finalized: string[] = [];

      for (let index = 0; index < event.results.length; index += 1) {
        const result = event.results[index];
        const transcript = result?.[0]?.transcript?.trim();

        if (!transcript) {
          continue;
        }

        preview = `${preview} ${transcript}`.trim();
        if (result.isFinal) {
          finalized.push(transcript);
        }
      }

      if (preview) {
        setTranscriptPreview(preview);
      }

      if (finalized.length) {
        const dictated = finalized.join(" ").trim();
        onInsertText(dictated);
        setStatusMessage(`Inserted dictated text into ${targetFieldLabel}.`);
      }
    };

    recognition.onerror = (event) => {
      setListening(false);
      setStatusMessage(`Speech input error: ${event.error || "unknown"}.`);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognition.start();
    recognitionRef.current = recognition;
    setListening(true);
    setStatusMessage(`Listening in ${selectedLocaleDetails.label}.`);
  };

  const toggleDictation = () => {
    if (listening) {
      stopSpeechInput();
      setStatusMessage("Speech dictation stopped.");
      return;
    }

    startDictation();
  };

  const speakNarration = () => {
    if (!narrationText) {
      setStatusMessage("Run the action first to generate a spoken summary.");
      return;
    }

    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setStatusMessage("This browser does not expose speech synthesis.");
      return;
    }

    stopNarration();

    const utterance = new SpeechSynthesisUtterance(narrationText);
    const localePrefix = selectedLocale.toLowerCase().split("-")[0];
    const voices = window.speechSynthesis.getVoices();
    const matchingVoice =
      voices.find((voice) => voice.lang.toLowerCase() === selectedLocale.toLowerCase()) ||
      voices.find((voice) => voice.lang.toLowerCase().startsWith(localePrefix));

    utterance.lang = selectedLocale;
    if (matchingVoice) {
      utterance.voice = matchingVoice;
    }

    utterance.onstart = () => {
      setSpeaking(true);
      setStatusMessage(`Reading the latest result in ${selectedLocaleDetails.label}.`);
    };

    utterance.onend = () => {
      setSpeaking(false);
    };

    utterance.onerror = () => {
      setSpeaking(false);
      setStatusMessage("Speech synthesis could not complete.");
    };

    window.speechSynthesis.speak(utterance);
  };

  const runGesture = (gesture: "submit" | "speak" | "clear" | "stop" | "dictate") => {
    if (gesture === "submit") {
      onSubmit();
      setStatusMessage("Swipe right submitted the current action.");
      return;
    }

    if (gesture === "speak") {
      speakNarration();
      return;
    }

    if (gesture === "clear") {
      if (!textFields.length || !targetField) {
        setStatusMessage("Swipe down is available when a text field is selected.");
        return;
      }

      onClearTargetField();
      setTranscriptPreview("");
      setStatusMessage(`Cleared ${targetFieldLabel}.`);
      return;
    }

    if (gesture === "stop") {
      stopSpeechInput();
      stopNarration();
      setStatusMessage("Stopped dictation and read-aloud.");
      return;
    }

    toggleDictation();
  };

  const handleGestureStart = (event: React.PointerEvent<HTMLDivElement>) => {
    gestureStartRef.current = {
      pointerId: event.pointerId,
      x: event.clientX,
      y: event.clientY,
      startedAt: Date.now(),
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const handleGestureEnd = (event: React.PointerEvent<HTMLDivElement>) => {
    const start = gestureStartRef.current;
    gestureStartRef.current = null;

    if (!start || start.pointerId !== event.pointerId) {
      return;
    }

    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    const duration = Date.now() - start.startedAt;
    const distance = Math.hypot(dx, dy);

    if (duration >= 700 && distance < 24) {
      runGesture("dictate");
      return;
    }

    if (Math.abs(dx) >= Math.abs(dy) && Math.abs(dx) > 48) {
      runGesture(dx > 0 ? "submit" : "stop");
      return;
    }

    if (Math.abs(dy) > 48) {
      runGesture(dy < 0 ? "speak" : "clear");
      return;
    }

    setStatusMessage("Gesture not recognized. Use a firmer swipe or a long press.");
  };

  return (
    <Card className="mt-6 border-slate-200 bg-slate-50/80 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Assistive Input</div>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
            Voice dictation, read-aloud, and low-friction gesture shortcuts for the current action. The panel includes all 22
            scheduled Indian languages plus English (India) for browser-based speech controls.
          </p>
        </div>
        <Badge variant="default" className="border-slate-200 bg-white text-slate-700">
          {indianAssistiveLocales.length} Indian languages
        </Badge>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor="assistive-locale" className="text-sm font-medium text-slate-700">
                Voice locale
              </label>
              <Select
                id="assistive-locale"
                name="assistiveLocale"
                className="mt-2"
                options={assistiveLocales.map((locale) => locale.code)}
                value={selectedLocale}
                onChange={(event: React.ChangeEvent<HTMLSelectElement>) => setSelectedLocale(event.target.value)}
              />
              <div className="mt-2 text-xs text-slate-500">
                {selectedLocaleDetails.label} · {selectedLocaleDetails.nativeLabel} · {selectedLocaleDetails.script}
              </div>
            </div>

            <div>
              <label htmlFor="assistive-target" className="text-sm font-medium text-slate-700">
                Target text field
              </label>
              <Select
                id="assistive-target"
                name="assistiveTarget"
                className="mt-2"
                options={textFields.map((field) => field.name)}
                value={targetField || ""}
                onChange={(event: React.ChangeEvent<HTMLSelectElement>) => onTargetFieldChange(event.target.value)}
                disabled={!textFields.length}
              />
              <div className="mt-2 text-xs text-slate-500">
                {textFields.length ? `Current target: ${targetFieldLabel}` : "This action has no free-text field for dictation."}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={toggleDictation} disabled={!recognitionConstructor || !textFields.length}>
              {listening ? "Stop Dictation" : "Start Dictation"}
            </Button>
            <Button type="button" variant="secondary" onClick={speakNarration}>
              {speaking ? "Reading..." : "Read Result"}
            </Button>
            <Button type="button" variant="outline" onClick={() => runGesture("clear")} disabled={!textFields.length || !targetField}>
              Clear Target
            </Button>
            <Button type="button" variant="outline" onClick={() => runGesture("stop")}>
              Stop Audio
            </Button>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700" aria-live="polite">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Status</div>
            <div className="mt-2">{statusMessage}</div>
            {transcriptPreview ? <div className="mt-2 text-slate-500">Latest transcript: {transcriptPreview}</div> : null}
          </div>
        </div>

        <div className="space-y-4">
          <div
            className="rounded-2xl border border-dashed border-[#115E59]/30 bg-[#115E59]/5 p-5 text-sm text-slate-700 touch-none"
            onPointerDown={handleGestureStart}
            onPointerUp={handleGestureEnd}
            onPointerCancel={() => {
              gestureStartRef.current = null;
            }}
          >
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#115E59]">Gesture Pad</div>
            <div className="mt-3 text-sm leading-relaxed">
              Long press toggles dictation. Swipe right submits. Swipe up reads the latest result. Swipe down clears the
              current text field. Swipe left stops speech.
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Indian Language Coverage</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {indianAssistiveLocales.map((locale) => (
                <span key={locale.code} className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
                  {locale.nativeLabel}
                </span>
              ))}
            </div>
            <div className="mt-3 text-xs leading-relaxed text-slate-500">
              Browser speech engines decide which locales are recognized or voiced on a given device, but the app now exposes the full
              language set and gracefully falls back when a locale is unavailable.
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
