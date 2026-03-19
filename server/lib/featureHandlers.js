import { featureMap } from "../../shared/featureCatalog.js";
import { extractTextFromFiles } from "./analysis.js";
import { getModelSummary, inferWithModelService } from "./modelService.js";

function sanitizeFiles(files = []) {
  return files.map((file) => ({
    name: file.originalname,
    type: file.mimetype,
    size: file.size,
  }));
}

export async function getDashboardSummary() {
  return getModelSummary();
}

export async function executeFeature(featureId, actionId, actionInput = {}, files = [], session = {}) {
  const feature = featureMap[featureId];
  if (!feature) {
    throw new Error("Unknown feature requested.");
  }

  const action = feature.actions.find((candidate) => candidate.id === actionId);
  if (!action) {
    throw new Error("Unknown feature action requested.");
  }

  const extracted = await extractTextFromFiles(files);
  const payload = {
    ...actionInput,
    __extractedText: extracted.text,
    __fileNotes: extracted.notes,
    __files: sanitizeFiles(files),
  };

  const response = await inferWithModelService(featureId, actionId, payload, session);
  return {
    featureId,
    actionId,
    featureTitle: feature.title,
    actionLabel: action.label,
    result: response.result,
  };
}
