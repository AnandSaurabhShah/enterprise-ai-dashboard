import fs from "node:fs/promises";
import path from "node:path";

const dataDirectory = path.join(process.cwd(), "server", "data");

async function ensureDataDirectory() {
  await fs.mkdir(dataDirectory, { recursive: true });
}

function getStorePath(name) {
  return path.join(dataDirectory, `${name}.json`);
}

export async function readStore(name, fallback) {
  await ensureDataDirectory();
  const filePath = getStorePath(name);

  try {
    const raw = await fs.readFile(filePath, "utf8");
    return JSON.parse(raw);
  } catch (error) {
    if (error.code === "ENOENT") {
      await writeStore(name, fallback);
      return fallback;
    }

    throw error;
  }
}

export async function writeStore(name, value) {
  await ensureDataDirectory();
  const filePath = getStorePath(name);
  await fs.writeFile(filePath, JSON.stringify(value, null, 2), "utf8");
  return value;
}
