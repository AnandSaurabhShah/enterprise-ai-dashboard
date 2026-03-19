import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router";

import { AssistiveControls } from "../components/AssistiveControls";
import { FeatureResult } from "../components/FeatureResult";
import { featureMap } from "../data/features";
import { buildNarrationText } from "../lib/assistive";
import { runFeatureAction } from "../lib/api";
import { Badge, Button, Card, Input, Select, Textarea } from "../components/ui";

type Field = {
  name: string;
  label: string;
  type: string;
  placeholder?: string;
  options?: string[];
  defaultValue?: string;
  required?: boolean;
  accept?: string;
};

function buildInitialState(feature: any) {
  return feature.actions.reduce((state: Record<string, any>, action: any) => {
    action.fields.forEach((field: Field) => {
      state[field.name] = field.type === "file" ? null : field.defaultValue || "";
    });
    return state;
  }, {});
}

function textInputFields(action: any) {
  return action.fields.filter((field: Field) => field.type === "text" || field.type === "textarea");
}

function buildAssistiveTargets(feature: any) {
  if (!feature) {
    return {};
  }

  return feature.actions.reduce((state: Record<string, string>, action: any) => {
    state[action.id] = textInputFields(action)[0]?.name || "";
    return state;
  }, {});
}

export function FeaturePage() {
  const { featureId } = useParams();
  const feature = featureId ? featureMap[featureId] : undefined;
  const initialState = useMemo(() => (feature ? buildInitialState(feature) : {}), [feature]);
  const initialTargets = useMemo(() => buildAssistiveTargets(feature), [feature]);
  const [values, setValues] = useState<Record<string, any>>(initialState);
  const [loadingAction, setLoadingAction] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Record<string, any>>({});
  const [assistiveTargets, setAssistiveTargets] = useState<Record<string, string>>(initialTargets);

  useEffect(() => {
    setValues(initialState);
    setLoadingAction("");
    setErrors({});
    setResults({});
    setAssistiveTargets(initialTargets);
  }, [initialState, initialTargets]);

  if (!feature) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#F9F8F4] p-12 text-slate-500">
        <h2 className="mb-2 text-2xl font-bold text-slate-900">Feature not found</h2>
        <p>The requested feature module could not be located.</p>
        <Link to="/dashboard" className="mt-6 font-medium text-[#115E59] hover:underline">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const handleChange = (field: Field, value: unknown) => {
    setValues((current) => ({
      ...current,
      [field.name]: value,
    }));
  };

  const handleAssistiveTargetChange = (actionId: string, fieldName: string) => {
    setAssistiveTargets((current) => ({
      ...current,
      [actionId]: fieldName,
    }));
  };

  const handleAssistiveInsert = (action: any, transcript: string) => {
    const fields = textInputFields(action);
    const targetFieldName = assistiveTargets[action.id] || fields[0]?.name;
    const targetField = action.fields.find((field: Field) => field.name === targetFieldName);

    if (!targetField || !transcript.trim()) {
      return;
    }

    setValues((current) => {
      const existing = String(current[targetField.name] || "");
      const separator = targetField.type === "textarea" && existing ? "\n" : existing ? " " : "";

      return {
        ...current,
        [targetField.name]: `${existing}${separator}${transcript.trim()}`.trim(),
      };
    });
  };

  const handleAssistiveClear = (action: any) => {
    const fields = textInputFields(action);
    const targetFieldName = assistiveTargets[action.id] || fields[0]?.name;

    if (!targetFieldName) {
      return;
    }

    setValues((current) => ({
      ...current,
      [targetFieldName]: "",
    }));
  };

  const handleSubmit = async (action: any) => {
    setLoadingAction(action.id);
    setErrors((current) => ({ ...current, [action.id]: "" }));

    try {
      const payload = action.fields.reduce((result: Record<string, unknown>, field: Field) => {
        result[field.name] = values[field.name];
        return result;
      }, {});
      const response = await runFeatureAction(feature.id, action.id, payload);
      setResults((current) => ({ ...current, [action.id]: response }));
    } catch (caughtError) {
      setErrors((current) => ({
        ...current,
        [action.id]: caughtError instanceof Error ? caughtError.message : "Action failed.",
      }));
    } finally {
      setLoadingAction("");
    }
  };

  const renderField = (action: any, field: Field) => {
    const commonProps = {
      id: `${action.id}-${field.name}`,
      name: field.name,
    };

    if (field.type === "textarea") {
      return (
        <Textarea
          {...commonProps}
          className="min-h-[140px]"
          placeholder={field.placeholder}
          value={values[field.name] || ""}
          onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) => handleChange(field, event.target.value)}
          onFocus={() => handleAssistiveTargetChange(action.id, field.name)}
          required={field.required}
        />
      );
    }

    if (field.type === "select") {
      return (
        <Select
          {...commonProps}
          options={field.options || []}
          value={values[field.name] || field.defaultValue || ""}
          onChange={(event: React.ChangeEvent<HTMLSelectElement>) => handleChange(field, event.target.value)}
        />
      );
    }

    if (field.type === "file") {
      return (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4">
          <input
            {...commonProps}
            type="file"
            accept={field.accept}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => handleChange(field, event.target.files?.[0] || null)}
          />
          <div className="mt-3 text-xs text-slate-500">{values[field.name]?.name || "No file selected yet."}</div>
        </div>
      );
    }

    return (
        <Input
          {...commonProps}
          type={field.type === "number" ? "number" : "text"}
          placeholder={field.placeholder}
          value={values[field.name] || ""}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => handleChange(field, event.target.value)}
          onFocus={() => {
            if (field.type === "text") {
              handleAssistiveTargetChange(action.id, field.name);
            }
          }}
          required={field.required}
        />
      );
  };

  return (
    <div className="min-h-screen bg-[#F9F8F4] px-6 py-8 lg:px-10 lg:py-10">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex flex-wrap items-center gap-3 text-sm text-slate-500">
          <Link to="/dashboard" className="transition-colors hover:text-slate-900">
            Dashboard
          </Link>
          <span>/</span>
          <span>{feature.status === "live" ? "Live Tools" : "Expanded Modules"}</span>
          <span>/</span>
          <span className="font-medium text-slate-900">{feature.title}</span>
        </div>

        <div className="mb-10">
          <div className="mb-4 flex flex-wrap items-center gap-4">
            <Badge variant={feature.status === "live" ? "live" : "preview"} className="px-3 py-1 text-sm shadow-sm">
              {feature.status === "live" ? "LIVE MODULE" : "BETA MODULE"}
            </Badge>
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">{feature.category}</span>
          </div>
          <h1 className="font-serif text-4xl font-bold tracking-tight text-slate-900 lg:text-5xl">{feature.title}</h1>
          <p className="mt-4 max-w-3xl text-lg text-slate-600">{feature.description}</p>
        </div>

        <div className="space-y-8">
          {feature.actions.map((action: any) => (
            <div key={action.id} className="grid gap-6 xl:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
              <Card className="border-slate-200 bg-white p-6 shadow-sm">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-400">{action.label}</div>
                <h2 className="mt-2 text-2xl font-bold text-slate-900">{action.submitLabel}</h2>
                <p className="mt-3 text-sm leading-relaxed text-slate-600">{action.description}</p>

                <div className="mt-6 space-y-4">
                  {action.fields.length ? (
                    action.fields.map((field: Field) => (
                      <div key={field.name} className="space-y-2">
                        <label htmlFor={`${action.id}-${field.name}`} className="text-sm font-medium text-slate-700">
                          {field.label}
                        </label>
                        {renderField(action, field)}
                      </div>
                    ))
                  ) : (
                    <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                      No additional input is required for this action.
                    </div>
                  )}
                </div>

                <AssistiveControls
                  textFields={textInputFields(action)}
                  targetField={assistiveTargets[action.id] || ""}
                  onTargetFieldChange={(fieldName) => handleAssistiveTargetChange(action.id, fieldName)}
                  onInsertText={(transcript) => handleAssistiveInsert(action, transcript)}
                  onClearTargetField={() => handleAssistiveClear(action)}
                  onSubmit={() => handleSubmit(action)}
                  narrationText={buildNarrationText(results[action.id]?.result)}
                />

                {errors[action.id] ? (
                  <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{errors[action.id]}</div>
                ) : null}

                <Button className="mt-6 w-full" onClick={() => handleSubmit(action)} disabled={loadingAction === action.id}>
                  {loadingAction === action.id ? "Working..." : action.submitLabel}
                </Button>
              </Card>

              <FeatureResult payload={results[action.id]} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
