import React from "react";
import { Card, Terminal } from "./ui";

type Section = {
  title: string;
  type: string;
  items?: Array<any>;
  rows?: Array<Record<string, unknown>>;
  content?: unknown;
};

function renderList(items: Array<any> = []) {
  return (
    <div className="space-y-3">
      {items.map((item, index) => {
        if (typeof item === "string") {
          return (
            <div key={`${item}-${index}`} className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {item}
            </div>
          );
        }

        return (
          <div key={index} className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <div className="font-semibold text-slate-900">{item.title || item.label || `Item ${index + 1}`}</div>
            <div className="mt-1 text-slate-600">{item.detail || item.value || JSON.stringify(item)}</div>
          </div>
        );
      })}
    </div>
  );
}

function renderKeyValue(items: Array<any> = []) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {items.map((item, index) => (
        <div key={`${item.label}-${index}`} className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400">{item.label}</div>
          <div className="mt-2 text-sm font-medium text-slate-800 break-words">{String(item.value)}</div>
        </div>
      ))}
    </div>
  );
}

function renderTable(rows: Array<Record<string, unknown>> = []) {
  if (!rows.length) {
    return <div className="text-sm text-slate-500">No rows returned.</div>;
  }

  const columns = Object.keys(rows[0]);

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((column) => (
              <th key={column} className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-500">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column) => (
                <td key={`${rowIndex}-${column}`} className="px-4 py-3 align-top text-slate-700">
                  {String(row[column] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderSection(section: Section) {
  switch (section.type) {
    case "list":
      return renderList(section.items);
    case "keyValue":
      return renderKeyValue(section.items);
    case "table":
      return renderTable(section.rows);
    case "json":
      return (
        <Terminal>
          <pre className="whitespace-pre-wrap text-xs">{JSON.stringify(section.content, null, 2)}</pre>
        </Terminal>
      );
    case "text":
    default:
      return <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">{String(section.content || "")}</div>;
  }
}

export function FeatureResult({ payload }: { payload: any }) {
  if (!payload?.result) {
    return <Terminal>Run the action to see live output here.</Terminal>;
  }

  const result = payload.result;

  return (
    <div className="space-y-6">
      <Card className="border-slate-200 bg-[#0F172A] p-6 text-white shadow-lg">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">{payload.actionLabel}</div>
        <h3 className="mt-3 text-2xl font-bold text-white">{result.headline}</h3>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-300">{result.summary}</p>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {(result.metrics || []).map((metric: any) => (
          <Card key={metric.label} className="border-slate-200 bg-white p-4">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">{metric.label}</div>
            <div className="mt-2 text-lg font-semibold text-slate-900">{metric.value}</div>
          </Card>
        ))}
      </div>

      {result.highlights?.length ? (
        <Card className="border-slate-200 bg-white p-6">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Highlights</div>
          <div className="mt-4 space-y-3">
            {result.highlights.map((item: string, index: number) => (
              <div key={`${item}-${index}`} className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                {item}
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {(result.sections || []).map((section: Section) => (
        <Card key={section.title} className="border-slate-200 bg-white p-6">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400">{section.title}</div>
          <div className="mt-4">{renderSection(section)}</div>
        </Card>
      ))}

      {result.notes?.length ? (
        <Terminal>
          {result.notes.map((note: string, index: number) => (
            <div key={`${note}-${index}`}>{note}</div>
          ))}
        </Terminal>
      ) : null}
    </div>
  );
}
