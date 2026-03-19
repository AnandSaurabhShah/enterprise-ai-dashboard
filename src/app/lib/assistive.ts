export type AssistiveLocale = {
  code: string;
  label: string;
  nativeLabel: string;
  script: string;
  indian: boolean;
};

export const assistiveLocales: AssistiveLocale[] = [
  { code: "en-IN", label: "English (India)", nativeLabel: "English", script: "Latin", indian: false },
  { code: "as-IN", label: "Assamese", nativeLabel: "অসমীয়া", script: "Bengali-Assamese", indian: true },
  { code: "bn-IN", label: "Bengali", nativeLabel: "বাংলা", script: "Bengali-Assamese", indian: true },
  { code: "brx-IN", label: "Bodo", nativeLabel: "बर'", script: "Devanagari", indian: true },
  { code: "doi-IN", label: "Dogri", nativeLabel: "डोगरी", script: "Devanagari", indian: true },
  { code: "gu-IN", label: "Gujarati", nativeLabel: "ગુજરાતી", script: "Gujarati", indian: true },
  { code: "hi-IN", label: "Hindi", nativeLabel: "हिन्दी", script: "Devanagari", indian: true },
  { code: "kn-IN", label: "Kannada", nativeLabel: "ಕನ್ನಡ", script: "Kannada", indian: true },
  { code: "ks-IN", label: "Kashmiri", nativeLabel: "कॉशुर / كٲشُر", script: "Devanagari-Perso-Arabic", indian: true },
  { code: "gom-IN", label: "Konkani", nativeLabel: "कोंकणी", script: "Devanagari", indian: true },
  { code: "mai-IN", label: "Maithili", nativeLabel: "मैथिली", script: "Devanagari", indian: true },
  { code: "ml-IN", label: "Malayalam", nativeLabel: "മലയാളം", script: "Malayalam", indian: true },
  { code: "mni-IN", label: "Manipuri", nativeLabel: "মৈতৈলোন্", script: "Bengali-Meitei", indian: true },
  { code: "mr-IN", label: "Marathi", nativeLabel: "मराठी", script: "Devanagari", indian: true },
  { code: "ne-NP", label: "Nepali", nativeLabel: "नेपाली", script: "Devanagari", indian: true },
  { code: "or-IN", label: "Odia", nativeLabel: "ଓଡ଼ିଆ", script: "Odia", indian: true },
  { code: "pa-IN", label: "Punjabi", nativeLabel: "ਪੰਜਾਬੀ", script: "Gurmukhi", indian: true },
  { code: "sa-IN", label: "Sanskrit", nativeLabel: "संस्कृतम्", script: "Devanagari", indian: true },
  { code: "sat-IN", label: "Santali", nativeLabel: "ᱥᱟᱱᱛᱟᱲᱤ", script: "Ol Chiki", indian: true },
  { code: "sd-IN", label: "Sindhi", nativeLabel: "सिन्धी / سنڌي", script: "Devanagari-Perso-Arabic", indian: true },
  { code: "ta-IN", label: "Tamil", nativeLabel: "தமிழ்", script: "Tamil", indian: true },
  { code: "te-IN", label: "Telugu", nativeLabel: "తెలుగు", script: "Telugu", indian: true },
  { code: "ur-IN", label: "Urdu", nativeLabel: "اردو", script: "Perso-Arabic", indian: true },
];

export const indianAssistiveLocales = assistiveLocales.filter((locale) => locale.indian);

export function describeAssistiveLocale(code: string) {
  return assistiveLocales.find((locale) => locale.code === code) || assistiveLocales[0];
}

export function buildNarrationText(result: any) {
  if (!result) {
    return "";
  }

  const highlights = Array.isArray(result.highlights) ? result.highlights.slice(0, 3).join(". ") : "";
  return [result.headline, result.summary, highlights]
    .filter(Boolean)
    .join(". ")
    .replace(/\s+/g, " ")
    .trim();
}
