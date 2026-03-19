import crypto from "node:crypto";

import cors from "cors";
import express from "express";
import multer from "multer";

import { featureCatalog } from "../shared/featureCatalog.js";
import { executeFeature, getDashboardSummary } from "./lib/featureHandlers.js";

const app = express();
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 25 * 1024 * 1024 } });
const port = Number(process.env.PORT || 8787);
const sessionSecret = process.env.SESSION_SECRET || "enterprise-ai-local-secret";

app.use(cors());
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

function signToken(session) {
  const payload = Buffer.from(JSON.stringify(session)).toString("base64url");
  const signature = crypto.createHmac("sha256", sessionSecret).update(payload).digest("hex");
  return `${payload}.${signature}`;
}

function verifyToken(token) {
  const [payload, signature] = token.split(".");
  if (!payload || !signature) {
    return null;
  }

  const expected = crypto.createHmac("sha256", sessionSecret).update(payload).digest("hex");
  if (expected !== signature) {
    return null;
  }

  try {
    return JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
  } catch {
    return null;
  }
}

function deriveName(email = "") {
  const localPart = email.split("@")[0] || "demo user";
  return localPart
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function requireAuth(req, res, next) {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  const session = verifyToken(token);

  if (!session) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }

  req.session = session;
  next();
}

app.get("/api/health", (_req, res) => {
  res.json({
    ok: true,
    service: "enterprise-ai-backend",
    now: new Date().toISOString(),
  });
});

app.get("/api/catalog", (_req, res) => {
  res.json({ features: featureCatalog });
});

app.post("/api/auth/login", (req, res) => {
  const email = String(req.body.email || "").trim().toLowerCase();
  const password = String(req.body.password || "");
  const provider = String(req.body.provider || "password");

  if (!email) {
    res.status(400).json({ error: "Email is required." });
    return;
  }

  if (provider === "password" && !password) {
    res.status(400).json({ error: "Password is required." });
    return;
  }

  const session = {
    email,
    name: deriveName(email),
    provider,
    workspace: "Enterprise AI Demo",
    issuedAt: new Date().toISOString(),
  };

  res.json({
    token: signToken(session),
    user: session,
  });
});

app.get("/api/dashboard/summary", requireAuth, async (_req, res, next) => {
  try {
    const summary = await getDashboardSummary();
    res.json(summary);
  } catch (error) {
    next(error);
  }
});

app.post("/api/features/:featureId/:actionId", requireAuth, upload.any(), async (req, res, next) => {
  try {
    const payload = await executeFeature(
      req.params.featureId,
      req.params.actionId,
      req.body,
      req.files || [],
      req.session
    );
    res.json(payload);
  } catch (error) {
    next(error);
  }
});

app.use((error, _req, res, _next) => {
  const status = error.message === "Unauthorized" ? 401 : 400;
  res.status(status).json({
    error: error.message || "Unexpected server error.",
  });
});

app.listen(port, () => {
  console.log(`Enterprise AI backend listening on http://localhost:${port}`);
});
