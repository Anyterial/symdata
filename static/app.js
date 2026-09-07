const tableView = document.getElementById("table-view");
const indexTable = document.getElementById("index-table");
const tableHead = document.getElementById("table-head");
const tableBody = document.getElementById("table-body");
const searchInput = document.getElementById("search-input");
const searchSummary = document.getElementById("search-summary");
const emptyState = document.getElementById("empty-state");
const settingsToggleWrapIndex = document.getElementById("settings-toggle-wrap-index");

const INDEX_FIELDS = [
  "hall_key",
  "hall_entry",
  "hall",
  "hall_latex",
  "hall_html",
  "hall_unicode",
  "hall_aliases",
  "hall_aliases_latex",
  "hall_aliases_html",
  "hall_aliases_unicode",
  "hm_entry",
  "hm_entry_aliases",
  "hm_entry_latex",
  "hm_entry_html",
  "hm_entry_unicode",
  "ita_number",
  "hm_short",
  "hm_short_aliases",
  "hm_short_aliases_latex",
  "hm_short_aliases_html",
  "hm_short_aliases_unicode",
  "hm_short_latex",
  "hm_short_html",
  "hm_short_unicode",
  "hm_full",
  "hm_full_latex",
  "hm_full_html",
  "hm_full_unicode",
  "hm_extended",
  "hm_extended_latex",
  "hm_extended_html",
  "hm_extended_unicode",
  "hm_universal",
  "hm_universal_aliases",
  "hm_universal_aliases_latex",
  "hm_universal_aliases_html",
  "hm_universal_aliases_unicode",
  "hm_universal_latex",
  "hm_universal_html",
  "hm_universal_unicode",
  "short_hm_symbol",
  "short_hm_symbol_latex",
  "short_hm_symbol_unicode",
  "short_hm_symbol_aliases",
  "short_hm_symbol_aliases_latex",
  "universal_hm",
  "universal_hm_latex",
  "universal_hm_unicode",
  "n_c",
  "n_c_aliases",
  "setting_it_nc",
  "it_coordinate_system_code",
  "crystal_system",
  "point_group",
  "schoenflies_html",
  "is_reference_setting"
];

const INDEX_DATA_PATH = "data/spacegroup_index.json.gz";
const SYMMETRY_BASICS_DATA_PATH = "data/symmetry_basics.json.gz";
const POINTGROUP_INDEX_DATA_PATH = "data/pointgroup_index.json.gz";

const DATASET_SPACEGROUPS = "spacegroups";
const DATASET_POINTGROUPS = "pointgroups";
const FIELD_DOC_URLS = {
  hall: "https://schemas.httk.org/defs/v0.1/properties/spacegroups/hall",
  hm_entry: "https://schemas.httk.org/defs/v0.1/properties/spacegroups/hm_entry",
  hm_short: "https://schemas.httk.org/defs/v0.1/properties/spacegroups/hm_short",
  hm_full: "https://schemas.httk.org/defs/v0.1/properties/spacegroups/hm_full",
  hm_extended: "https://schemas.httk.org/defs/v0.1/properties/spacegroups/hm_extended",
  it_number: "https://schemas.httk.org/defs/v0.1/properties/spacegroups/it_number",
  setting_it_nc: "https://schemas.httk.org/defs/v0.1/properties/spacegroups/setting_it_nc"
};

const SETTINGS_ALL = "all";
const SETTINGS_ITA = "ita";
const SETTINGS_QUERY_KEY = "settings";
const SETTINGS_STORAGE_KEY = "spacegroup_settings_mode";
const THEME_QUERY_KEY = "theme";
const THEME_DARK = "dark";
const THEME_TWILIGHT = "twilight";
const THEME_LIGHT = "light";
const ALT_SETTINGS_QUERY_KEY = "alt_settings";
const SETTING_TRANSFORMS_QUERY_KEY = "setting_transforms";
const IDENTITY_QUERY_KEY = "identity";
const DETAILS_QUERY_KEY = "details";
const HARKER_QUERY_KEY = "harker";
const POINTGROUP_NAV_QUERY_KEY = "pointgroup_nav";
const SYMOPS_QUERY_KEY = "symops";
const WYCKOFF_QUERY_KEY = "wyckoff";
const MAX_SUBGROUPS_QUERY_KEY = "max_subgroups";
const MIN_SUPERGROUPS_QUERY_KEY = "min_supergroups";
const NORMALIZER_QUERY_KEY = "normalizer";
const K_SUBGROUPS_QUERY_KEY = "k_subgroups";
const CONJUGACY_QUERY_KEY = "conjugacy";
const CHAR_REAL_QUERY_KEY = "char_real";
const CHAR_COMPLEX_QUERY_KEY = "char_complex";
const QUERY_VALUE_OPEN = "open";
const QUERY_VALUE_CLOSED = "closed";
const TRIANGLE_OPEN = "\u25BE";
const TRIANGLE_CLOSED = "\u25B8";

const escapeHtml = (value) => {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
};

const formatValue = (value) => {
  if (value === null || value === undefined || value === "") {
    return "\u2014";
  }
  if (Array.isArray(value)) {
    return value.join(", ") || "\u2014";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return String(value);
};

const firstNonEmpty = (...values) => {
  for (let i = 0; i < values.length; i += 1) {
    const value = values[i];
    if (value === null || value === undefined) {
      continue;
    }
    if (typeof value === "string" && value.trim() === "") {
      continue;
    }
    return value;
  }
  return null;
};

const toMaybeNumber = (value) => {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return null;
};

const markupField = (row, base, kind) => {
  const direct = row[`${base}_${kind}`];
  if (direct !== null && direct !== undefined) {
    return direct;
  }
  const markup = row[`${base}_markup`];
  if (markup && typeof markup === "object" && !Array.isArray(markup)) {
    return markup[kind];
  }
  return null;
};

const aliasesMarkupField = (row, base, kind) => {
  const direct = row[`${base}_aliases_${kind}`];
  if (direct !== null && direct !== undefined) {
    return direct;
  }
  const markup = row[`${base}_aliases_markup`];
  if (Array.isArray(markup)) {
    const values = markup.map((item) => (item && typeof item === "object" ? item[kind] : null)).filter((item) => item !== null && item !== undefined);
    return values.length ? values : null;
  }
  return null;
};

const normalizeRow = (row) => {
  const normalized = { ...row };

  // hall_entry is the normalized lookup key (matching the dataset); hall and
  // its markups carry the display symbol.
  normalized.hall_entry = firstNonEmpty(row.hall_entry, row.hall_key);
  normalized.hall = firstNonEmpty(row.hall, row.hall_symbol, normalized.hall_entry);
  normalized.hall_html = firstNonEmpty(markupField(row, "hall", "html"), row.hall_html, row.hall_unicode, normalized.hall, normalized.hall_entry);
  normalized.hall_latex = firstNonEmpty(markupField(row, "hall", "latex"), row.hall_latex, normalized.hall, normalized.hall_entry);
  normalized.hall_unicode = firstNonEmpty(markupField(row, "hall", "unicode"), row.hall_unicode, normalized.hall, normalized.hall_entry);
  normalized.hall_aliases = firstNonEmpty(row.hall_aliases);
  normalized.hall_aliases_latex = firstNonEmpty(aliasesMarkupField(row, "hall", "latex"), row.hall_aliases_latex);
  normalized.hall_aliases_html = firstNonEmpty(aliasesMarkupField(row, "hall", "html"), row.hall_aliases_html, row.hall_alias_html);
  normalized.hall_aliases_unicode = firstNonEmpty(aliasesMarkupField(row, "hall", "unicode"), row.hall_aliases_unicode, normalized.hall_aliases);

  normalized.hm_entry = firstNonEmpty(row.hm_entry);
  normalized.hm_entry_aliases = firstNonEmpty(row.hm_entry_aliases);
  normalized.hm_entry_html = firstNonEmpty(markupField(row, "hm_entry", "html"), row.hm_entry_html, normalized.hm_entry);
  normalized.hm_entry_latex = firstNonEmpty(markupField(row, "hm_entry", "latex"), row.hm_entry_latex, normalized.hm_entry);
  normalized.hm_entry_unicode = firstNonEmpty(markupField(row, "hm_entry", "unicode"), row.hm_entry_unicode, normalized.hm_entry);

  normalized.hm_short = firstNonEmpty(row.hm_short, row.short_hm_symbol);
  normalized.hm_short_aliases = firstNonEmpty(row.hm_short_aliases, row.short_hm_symbol_aliases);
  normalized.hm_short_aliases_latex = firstNonEmpty(aliasesMarkupField(row, "hm_short", "latex"), row.hm_short_aliases_latex, row.short_hm_symbol_aliases_latex);
  normalized.hm_short_aliases_html = firstNonEmpty(aliasesMarkupField(row, "hm_short", "html"), row.hm_short_aliases_html);
  normalized.hm_short_aliases_unicode = firstNonEmpty(aliasesMarkupField(row, "hm_short", "unicode"), row.hm_short_aliases_unicode, row.hm_short_aliases, row.short_hm_symbol_aliases);
  normalized.hm_short_html = firstNonEmpty(markupField(row, "hm_short", "html"), row.hm_short_html, row.hm_short);
  normalized.hm_short_latex = firstNonEmpty(markupField(row, "hm_short", "latex"), row.hm_short_latex, row.short_hm_symbol_latex, row.hm_short);
  normalized.hm_short_unicode = firstNonEmpty(markupField(row, "hm_short", "unicode"), row.hm_short_unicode, row.short_hm_symbol_unicode, row.hm_short);

  normalized.hm_full = firstNonEmpty(row.hm_full);
  normalized.hm_full_html = firstNonEmpty(markupField(row, "hm_full", "html"), row.hm_full_html, row.hm_full);
  normalized.hm_full_latex = firstNonEmpty(markupField(row, "hm_full", "latex"), row.hm_full_latex, row.hm_full);
  normalized.hm_full_unicode = firstNonEmpty(markupField(row, "hm_full", "unicode"), row.hm_full_unicode, row.hm_full);

  normalized.hm_extended = firstNonEmpty(row.hm_extended);
  normalized.hm_extended_html = firstNonEmpty(markupField(row, "hm_extended", "html"), row.hm_extended_html, row.hm_extended);
  normalized.hm_extended_latex = firstNonEmpty(markupField(row, "hm_extended", "latex"), row.hm_extended_latex, row.hm_extended);
  normalized.hm_extended_unicode = firstNonEmpty(markupField(row, "hm_extended", "unicode"), row.hm_extended_unicode, row.hm_extended);

  normalized.hm_universal = firstNonEmpty(row.hm_universal, row.hm_cctbx_universal, row.universal_hm);
  normalized.hm_universal_aliases = firstNonEmpty(row.hm_universal_aliases);
  normalized.hm_universal_aliases_latex = firstNonEmpty(row.hm_universal_aliases_latex, row.hm_universal_aliases);
  normalized.hm_universal_aliases_html = firstNonEmpty(row.hm_universal_aliases_html);
  normalized.hm_universal_aliases_unicode = firstNonEmpty(row.hm_universal_aliases_unicode, row.hm_universal_aliases);
  normalized.hm_universal_html = firstNonEmpty(row.hm_universal_html, row.hm_universal);
  normalized.hm_universal_latex = firstNonEmpty(row.hm_universal_latex, row.universal_hm_latex, row.hm_universal);
  normalized.hm_universal_unicode = firstNonEmpty(row.hm_universal_unicode, row.universal_hm_unicode, row.hm_universal);

  // Backfill legacy keys so older UI paths continue to work.
  normalized.short_hm_symbol = normalized.hm_short;
  normalized.short_hm_symbol_html = normalized.hm_short_html;
  normalized.short_hm_symbol_latex = normalized.hm_short_latex;
  normalized.short_hm_symbol_unicode = normalized.hm_short_unicode;
  normalized.short_hm_symbol_aliases = normalized.hm_short_aliases;
  normalized.short_hm_symbol_aliases_html = normalized.hm_short_aliases_html;
  normalized.short_hm_symbol_aliases_latex = normalized.hm_short_aliases_latex;
  normalized.universal_hm = normalized.hm_universal;
  normalized.universal_hm_html = normalized.hm_universal_html;
  normalized.universal_hm_latex = normalized.hm_universal_latex;
  normalized.universal_hm_unicode = normalized.hm_universal_unicode;
  normalized.ita_number = firstNonEmpty(row.ita_number, row.it_number);
  normalized.it_number = firstNonEmpty(row.it_number, row.ita_number);
  normalized.n_c = firstNonEmpty(row.n_c, row.setting_it_nc);
  normalized.setting_it_nc = normalized.n_c;
  normalized.n_c_aliases = firstNonEmpty(row.n_c_aliases, row.setting_it_nc_aliases);

  return normalized;
};

const normalizeRows = (rows) => rows.map((row) => normalizeRow(row));

const slugifyPointgroupSymbol = (symbol) => {
  let text = String(symbol || "").trim().toLowerCase();
  if (!text) {
    return "pointgroup";
  }
  if (text.startsWith("-")) {
    text = `neg-${text.slice(1)}`;
  }
  text = text.replace(/\//g, "-over-");
  text = text.replace(/\*/g, "star");
  text = text.replace(/\"/g, "prime");
  text = text.replace(/\s+/g, "-");
  text = text.replace(/[^a-z0-9-]/g, "-");
  text = text.replace(/-+/g, "-").replace(/^-+|-+$/g, "");
  return text || "pointgroup";
};

const normalizePointgroupRow = (row) => {
  const normalized = { ...row };
  normalized.pointgroup_key = firstNonEmpty(row.pointgroup_key, row.hm_symbol);
  normalized.hm_symbol = firstNonEmpty(row.hm_symbol, row.pointgroup_key);
  normalized.schoenflies = firstNonEmpty(row.schoenflies);
  normalized.schoenflies_html = firstNonEmpty(markupField(row, "schoenflies", "html"), row.schoenflies_html, row.schoenflies);
  normalized.schoenflies_unicode = firstNonEmpty(markupField(row, "schoenflies", "unicode"), row.schoenflies_unicode, row.schoenflies);
  normalized.schoenflies_latex = firstNonEmpty(markupField(row, "schoenflies", "latex"), row.schoenflies_latex, row.schoenflies);
  normalized.crystal_system = firstNonEmpty(row.crystal_system);
  normalized.laue_class = firstNonEmpty(row.laue_class);
  normalized.order = toMaybeNumber(row.order);
  normalized.n_conjugacy_classes = toMaybeNumber(row.n_conjugacy_classes);
  normalized.is_centrosymmetric = Boolean(row.is_centrosymmetric);
  normalized.slug = firstNonEmpty(row.slug);
  return normalized;
};

const normalizeSettingsMode = (value) => {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim().toLowerCase();
  if (normalized === SETTINGS_ALL || normalized === SETTINGS_ITA) {
    return normalized;
  }
  return null;
};

const normalizeDatasetMode = (value) => {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim().toLowerCase();
  if (normalized === DATASET_SPACEGROUPS || normalized === DATASET_POINTGROUPS) {
    return normalized;
  }
  return null;
};

const normalizeThemeMode = (value) => {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim().toLowerCase();
  if (normalized === THEME_DARK || normalized === THEME_TWILIGHT || normalized === THEME_LIGHT) {
    return normalized;
  }
  return null;
};

const inferDatasetFromPath = () => {
  const path = window.location.pathname || "/";
  if (path.includes("/pointgroup/")) {
    return DATASET_POINTGROUPS;
  }
  return DATASET_SPACEGROUPS;
};

const inferDatasetFromContext = () => {
  if (tableView) {
    const pageDataset = normalizeDatasetMode(tableView.getAttribute("data-table-dataset"));
    if (pageDataset) {
      return pageDataset;
    }
  }
  return inferDatasetFromPath();
};

const getModeFromUrl = () => {
  try {
    const url = new URL(window.location.href);
    return normalizeSettingsMode(url.searchParams.get(SETTINGS_QUERY_KEY));
  } catch {
    return null;
  }
};

const getThemeFromUrl = () => {
  try {
    const url = new URL(window.location.href);
    return normalizeThemeMode(url.searchParams.get(THEME_QUERY_KEY));
  } catch {
    return null;
  }
};

const getSectionOpenFromUrl = (queryKey, defaultOpen = true) => {
  try {
    const url = new URL(window.location.href);
    const value = String(url.searchParams.get(queryKey) || "").trim().toLowerCase();
    if (value === QUERY_VALUE_OPEN) {
      return true;
    }
    if (value === QUERY_VALUE_CLOSED) {
      return false;
    }
  } catch {
    // Ignore URL parsing errors.
  }
  return defaultOpen;
};

const getModeFromStorage = () => {
  try {
    return normalizeSettingsMode(window.localStorage.getItem(SETTINGS_STORAGE_KEY));
  } catch {
    return null;
  }
};

const sortState = { key: "ita_number", direction: "asc" };
let allRows = [];
let pointgroupRows = [];
let filteredRows = [];
let settingsMode = getModeFromUrl() || getModeFromStorage() || SETTINGS_ITA;
let activeDataset = inferDatasetFromContext();
let themeMode = getThemeFromUrl() || THEME_TWILIGHT;
let sectionState = {
  alt_settings: getSectionOpenFromUrl(ALT_SETTINGS_QUERY_KEY, true),
  setting_transforms: getSectionOpenFromUrl(SETTING_TRANSFORMS_QUERY_KEY, true),
  harker: getSectionOpenFromUrl(HARKER_QUERY_KEY, true),
  identity: getSectionOpenFromUrl(IDENTITY_QUERY_KEY, true),
  details: getSectionOpenFromUrl(DETAILS_QUERY_KEY, false),
  pointgroup_nav: getSectionOpenFromUrl(POINTGROUP_NAV_QUERY_KEY, true),
  symops: getSectionOpenFromUrl(SYMOPS_QUERY_KEY, true),
  wyckoff: getSectionOpenFromUrl(WYCKOFF_QUERY_KEY, true),
  max_subgroups: getSectionOpenFromUrl(MAX_SUBGROUPS_QUERY_KEY, true),
  min_supergroups: getSectionOpenFromUrl(MIN_SUPERGROUPS_QUERY_KEY, true),
  normalizer: getSectionOpenFromUrl(NORMALIZER_QUERY_KEY, true),
  k_subgroups: getSectionOpenFromUrl(K_SUBGROUPS_QUERY_KEY, true),
  conjugacy: getSectionOpenFromUrl(CONJUGACY_QUERY_KEY, true),
  char_real: getSectionOpenFromUrl(CHAR_REAL_QUERY_KEY, true),
  char_complex: getSectionOpenFromUrl(CHAR_COMPLEX_QUERY_KEY, true)
};

const SECTION_QUERY_KEYS = {
  alt_settings: ALT_SETTINGS_QUERY_KEY,
  setting_transforms: SETTING_TRANSFORMS_QUERY_KEY,
  harker: HARKER_QUERY_KEY,
  identity: IDENTITY_QUERY_KEY,
  details: DETAILS_QUERY_KEY,
  pointgroup_nav: POINTGROUP_NAV_QUERY_KEY,
  symops: SYMOPS_QUERY_KEY,
  wyckoff: WYCKOFF_QUERY_KEY,
  max_subgroups: MAX_SUBGROUPS_QUERY_KEY,
  min_supergroups: MIN_SUPERGROUPS_QUERY_KEY,
  normalizer: NORMALIZER_QUERY_KEY,
  k_subgroups: K_SUBGROUPS_QUERY_KEY,
  conjugacy: CONJUGACY_QUERY_KEY,
  char_real: CHAR_REAL_QUERY_KEY,
  char_complex: CHAR_COMPLEX_QUERY_KEY
};

const applyTheme = () => {
  const normalizedTheme = normalizeThemeMode(themeMode) || THEME_TWILIGHT;
  themeMode = normalizedTheme;
  document.documentElement.setAttribute("data-theme", normalizedTheme);
};

applyTheme();

const sortRows = (rows) => {
  const { key, direction } = sortState;
  const scalar = direction === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    const aRaw = a[key];
    const bRaw = b[key];
    const aValue = Array.isArray(aRaw) ? aRaw.join(",") : aRaw;
    const bValue = Array.isArray(bRaw) ? bRaw.join(",") : bRaw;

    if (aValue === null || aValue === undefined) {
      return 1;
    }
    if (bValue === null || bValue === undefined) {
      return -1;
    }

    if (typeof aValue === "number" && typeof bValue === "number") {
      return (aValue - bValue) * scalar;
    }
    return String(aValue).localeCompare(String(bValue), undefined, { numeric: true }) * scalar;
  });
};

const resolveBase = () => {
  const explicit = typeof window.SPACEGROUP_BASE_URL === "string" ? window.SPACEGROUP_BASE_URL : "";
  if (explicit) {
    try {
      const url = new URL(explicit, window.location.origin);
      const basePath = url.pathname || "/";
      return basePath.endsWith("/") ? basePath : `${basePath}/`;
    } catch {
      return explicit.endsWith("/") ? explicit : `${explicit}/`;
    }
  }

  if (document.currentScript && document.currentScript.src) {
    try {
      const url = new URL(document.currentScript.src, window.location.origin);
      const basePath = url.pathname.replace(/app\\.js(?:\\?.*)?$/, "");
      return basePath.endsWith("/") ? basePath : `${basePath}/`;
    } catch {
      // Ignore and fall through.
    }
  }

  const path = window.location.pathname || "/";
  if (path.includes("/hall/")) {
    return path.split("/hall/")[0] + "/";
  }
  if (path.includes("/pointgroup/")) {
    return path.split("/pointgroup/")[0] + "/";
  }
  return path.endsWith("/") ? path : path.replace(/[^/]+$/, "");
};

const readJsonResponse = async (response, source) => {
  if (!response.ok) {
    throw new Error(`Failed to load ${source} (${response.status})`);
  }

  const isGzipSource = source.endsWith(".gz");
  const contentEncoding = String(response.headers.get("content-encoding") || "").toLowerCase();
  if (!isGzipSource || contentEncoding.includes("gzip")) {
    return response.json();
  }

  if (typeof DecompressionStream !== "function" || !response.body) {
    throw new Error(`Browser cannot decompress gzip response for ${source}`);
  }

  const stream = response.body.pipeThrough(new DecompressionStream("gzip"));
  const text = await new Response(stream).text();
  return JSON.parse(text);
};

const withNavigationQuery = (targetPath, mode, theme = themeMode) => {
  const activeMode = normalizeSettingsMode(mode) || SETTINGS_ALL;
  const activeTheme = normalizeThemeMode(theme) || THEME_TWILIGHT;
  const url = new URL(targetPath, window.location.origin);
  url.searchParams.set(SETTINGS_QUERY_KEY, activeMode);
  url.searchParams.set(THEME_QUERY_KEY, activeTheme);
  Object.entries(SECTION_QUERY_KEYS).forEach(([key, queryKey]) => {
    url.searchParams.set(queryKey, sectionState[key] ? QUERY_VALUE_OPEN : QUERY_VALUE_CLOSED);
  });
  return `${url.pathname}${url.search}`;
};

const buildHallUrl = (baseUrl, hallKey, mode = settingsMode) => {
  const rawPath = `${baseUrl}hall/${encodeURIComponent(hallKey)}/`;
  return withNavigationQuery(rawPath, mode);
};

const buildPointgroupUrl = (baseUrl, slug) => {
  const rawPath = `${baseUrl}pointgroup/${encodeURIComponent(slug)}/`;
  return withNavigationQuery(rawPath, settingsMode);
};

const buildRootUrl = (baseUrl, mode = settingsMode, dataset = activeDataset) => {
  const normalizedDataset = normalizeDatasetMode(dataset) || DATASET_SPACEGROUPS;
  const rawPath = normalizedDataset === DATASET_POINTGROUPS ? `${baseUrl}pointgroup/` : baseUrl;
  return withNavigationQuery(rawPath, mode);
};

const syncModeUrlAndStorage = () => {
  const normalizedMode = normalizeSettingsMode(settingsMode) || SETTINGS_ALL;
  const normalizedTheme = normalizeThemeMode(themeMode) || THEME_TWILIGHT;
  settingsMode = normalizedMode;
  themeMode = normalizedTheme;
  activeDataset = normalizeDatasetMode(activeDataset) || inferDatasetFromContext();
  applyTheme();

  try {
    window.localStorage.setItem(SETTINGS_STORAGE_KEY, normalizedMode);
  } catch {
    // Ignore storage failures.
  }

  try {
    const url = new URL(window.location.href);
    url.searchParams.set(SETTINGS_QUERY_KEY, normalizedMode);
    url.searchParams.set(THEME_QUERY_KEY, normalizedTheme);
    Object.entries(SECTION_QUERY_KEYS).forEach(([key, queryKey]) => {
      url.searchParams.set(queryKey, sectionState[key] ? QUERY_VALUE_OPEN : QUERY_VALUE_CLOSED);
    });
    const next = `${url.pathname}${url.search}${url.hash}`;
    const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (next !== current) {
      window.history.replaceState({}, "", next);
    }
  } catch {
    // Ignore URL update failures.
  }
};

const getRowsForMode = (rows) => {
  if (settingsMode !== SETTINGS_ITA) {
    return rows;
  }
  return rows.filter((row) => Boolean(row.is_reference_setting));
};

const isLikelyLatex = (value) => {
  return typeof value === "string" && (value.includes("\\(") || value.includes("$"));
};

const renderMaybeMath = (value) => {
  const text = escapeHtml(formatValue(value));
  if (isLikelyLatex(value)) {
    return `<span class="math-content">${text}</span>`;
  }
  return text;
};

const renderInlineLatex = (value) => {
  if (value === null || value === undefined || String(value).trim() === "") {
    return escapeHtml(formatValue(value));
  }
  return `<span class="math-content">\\(${escapeHtml(String(value))}\\)</span>`;
};

const renderInlineHtml = (value) => {
  if (value === null || value === undefined || String(value).trim() === "") {
    return escapeHtml(formatValue(value));
  }
  return `<span>${String(value)}</span>`;
};

const getArrayValues = (value) => {
  if (Array.isArray(value)) {
    return value.filter((item) => item !== null && item !== undefined && String(item).trim() !== "");
  }
  if (value === null || value === undefined) {
    return [];
  }
  const text = String(value).trim();
  return text ? [value] : [];
};

const normalizeDropdownSymbolLabel = (value) => {
  const text = String(value ?? "");
  // Convert combining overline (e.g. A̅) into a prefixed minus form (-A).
  return text.replace(/(.)\u0305/g, "-$1");
};

const renderHmWithAliases = (row) => {
  const shortHtml = firstNonEmpty(row.hm_short_html, row.short_hm_symbol_html);
  const shortLatex = firstNonEmpty(row.hm_short_latex, row.short_hm_symbol_latex);
  const baseLabel = shortHtml
    ? renderInlineHtml(shortHtml)
    : shortLatex
      ? renderInlineLatex(shortLatex)
      : escapeHtml(formatValue(row.hm_short_unicode || row.hm_short || row.short_hm_symbol));
  const aliasesHtml = getArrayValues(row.hm_short_aliases_html || row.short_hm_symbol_aliases_html);
  const aliasesLatex = getArrayValues(row.hm_short_aliases_latex || row.short_hm_symbol_aliases_latex);
  const aliasesUnicode = getArrayValues(row.hm_short_aliases_unicode);
  const aliasesPlain = getArrayValues(row.hm_short_aliases || row.short_hm_symbol_aliases);
  const aliases = aliasesHtml.length ? aliasesHtml : aliasesLatex.length ? aliasesLatex : aliasesUnicode.length ? aliasesUnicode : aliasesPlain;
  if (!aliases.length) {
    return baseLabel;
  }
  const aliasLabel = aliasesHtml.length
    ? aliases.map((item) => renderInlineHtml(item)).join(", ")
    : aliasesLatex.length
      ? aliases.map((item) => renderInlineLatex(item)).join(", ")
      : aliases.map((item) => escapeHtml(formatValue(item))).join(", ");
  return `${baseLabel}&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;&nbsp;&nbsp;<span class="table-aliases-muted">(${aliasLabel})</span>`;
};

const renderHallWithLatex = (row) => {
  const hallHtml = firstNonEmpty(row.hall_html);
  const hallLatex = firstNonEmpty(row.hall_latex);
  const baseLabel = hallHtml
    ? renderInlineHtml(hallHtml)
    : hallLatex
      ? renderInlineLatex(hallLatex)
      : escapeHtml(formatValue(row.hall_unicode || row.hall || row.hall_key));
  const aliasesHtml = getArrayValues(row.hall_aliases_html);
  const aliasesLatex = getArrayValues(row.hall_aliases_latex);
  const aliasesUnicode = getArrayValues(row.hall_aliases_unicode);
  const aliasesPlain = getArrayValues(row.hall_aliases);
  const aliases = aliasesHtml.length ? aliasesHtml : aliasesLatex.length ? aliasesLatex : aliasesUnicode.length ? aliasesUnicode : aliasesPlain;
  if (!aliases.length) {
    return baseLabel;
  }
  const aliasLabel = aliasesHtml.length
    ? aliases.map((item) => renderInlineHtml(item)).join(", ")
    : aliasesLatex.length
      ? aliases.map((item) => renderInlineLatex(item)).join(", ")
      : aliases.map((item) => escapeHtml(formatValue(item))).join(", ");
  return `${baseLabel}&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;&nbsp;&nbsp;<span class="table-aliases-muted">(${aliasLabel})</span>`;
};

const renderHmEntry = (row) => {
  const entryHtml = firstNonEmpty(row.hm_entry_html);
  const entryLatex = firstNonEmpty(row.hm_entry_latex);
  const baseLabel = entryHtml
    ? renderInlineHtml(entryHtml)
    : entryLatex
      ? renderInlineLatex(entryLatex)
      : escapeHtml(formatValue(row.hm_entry || row.hm_full || row.hm_short));
  const aliasesHtml = getArrayValues(row.hm_entry_aliases_html);
  const aliasesLatex = getArrayValues(row.hm_entry_aliases_latex);
  const aliasesUnicode = getArrayValues(row.hm_entry_aliases_unicode);
  const aliasesPlain = getArrayValues(row.hm_entry_aliases);
  const aliases = aliasesHtml.length ? aliasesHtml : aliasesLatex.length ? aliasesLatex : aliasesUnicode.length ? aliasesUnicode : aliasesPlain;
  if (!aliases.length) {
    return baseLabel;
  }
  const aliasLabel = aliasesHtml.length
    ? aliases.map((item) => renderInlineHtml(item)).join(", ")
    : aliasesLatex.length
      ? aliases.map((item) => renderInlineLatex(item)).join(", ")
      : aliases.map((item) => escapeHtml(formatValue(item))).join(", ");
  return `${baseLabel}&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;&nbsp;&nbsp;<span class="table-aliases-muted">(${aliasLabel})</span>`;
};

const renderPointgroupSymbol = (row) => {
  return escapeHtml(formatValue(row.hm_symbol || row.pointgroup_key));
};

const renderPointgroupSchoenflies = (row) => {
  if (row.schoenflies_html) {
    return renderInlineHtml(row.schoenflies_html);
  }
  return renderMaybeMath(row.schoenflies_unicode || row.schoenflies || row.schoenflies_latex);
};

const TABLE_CONFIGS = {
  [DATASET_SPACEGROUPS]: {
    ariaLabel: "Spacegroup table",
    searchPlaceholder: "Hall symbol, H-M entry, HM symbol, IT number, n:c, crystal system...",
    emptyLabel: "spacegroups",
    defaultSortKey: "ita_number",
    columns: [
      { key: "short_hm_symbol", label: "Hermann-Mauguin", docUrl: FIELD_DOC_URLS.hm_short, render: (row) => renderHmWithAliases(row) },
      { key: "ita_number", label: "IT #", docUrl: FIELD_DOC_URLS.it_number, render: (row) => escapeHtml(formatValue(row.ita_number)) },
      { key: "hm_entry", label: "H-M Entry", docUrl: FIELD_DOC_URLS.hm_entry, render: (row) => renderHmEntry(row) },
      { key: "hall_key", label: "Hall Symbol", docUrl: FIELD_DOC_URLS.hall, render: (row) => renderHallWithLatex(row) },
      { key: "crystal_system", label: "Crystal System", muted: true, render: (row) => escapeHtml(formatValue(row.crystal_system)) },
      { key: "point_group", label: "Point Group", muted: true, render: (row) => escapeHtml(formatValue(row.point_group)) },
      { key: "n_c", label: "n:c", muted: true, render: (row) => escapeHtml([row.n_c, ...getArrayValues(row.n_c_aliases)].filter(Boolean).join(", ")) }
    ],
    rowUrl: (baseUrl, row) => buildHallUrl(baseUrl, row.hall_key)
  },
  [DATASET_POINTGROUPS]: {
    ariaLabel: "Pointgroup table",
    searchPlaceholder: "Point group symbol, Schoenflies, crystal system, laue class...",
    emptyLabel: "pointgroups",
    defaultSortKey: "hm_symbol",
    columns: [
      { key: "hm_symbol", label: "Point Group", render: (row) => renderPointgroupSymbol(row) },
      { key: "schoenflies_unicode", label: "Schoenflies", render: (row) => renderPointgroupSchoenflies(row) },
      { key: "crystal_system", label: "Crystal System", muted: true, render: (row) => escapeHtml(formatValue(row.crystal_system)) },
      { key: "laue_class", label: "Laue Class", muted: true, render: (row) => escapeHtml(formatValue(row.laue_class)) },
      { key: "order", label: "Order", muted: true, render: (row) => escapeHtml(formatValue(row.order)) },
      {
        key: "n_conjugacy_classes",
        label: "Conj. Classes",
        muted: true,
        render: (row) => escapeHtml(formatValue(row.n_conjugacy_classes))
      }
    ],
    rowUrl: (baseUrl, row) => buildPointgroupUrl(baseUrl, row.slug || slugifyPointgroupSymbol(row.hm_symbol || row.pointgroup_key))
  }
};

const getActiveTableConfig = () => {
  return TABLE_CONFIGS[activeDataset] || TABLE_CONFIGS[DATASET_SPACEGROUPS];
};

const ensureSortKeyForActiveDataset = (forceDefault = false) => {
  const config = getActiveTableConfig();
  const keys = new Set(config.columns.map((column) => column.key));
  if (forceDefault || !keys.has(sortState.key)) {
    sortState.key = config.defaultSortKey;
    sortState.direction = "asc";
  }
};

const getActiveSourceRows = () => {
  if (activeDataset === DATASET_POINTGROUPS) {
    return pointgroupRows;
  }
  return getRowsForMode(allRows);
};

const filterSpacegroupRows = (rows, query) => {
  const q = String(query || "").trim().toLowerCase();
  if (!q) {
    return rows;
  }

  return rows.filter((item) => {
    const haystack = [
      item.hall_key,
      item.hall_entry,
      item.hall,
      item.hall_latex,
      item.hall_html,
      item.hall_unicode,
      Array.isArray(item.hall_aliases) ? item.hall_aliases.join(" ") : item.hall_aliases,
      Array.isArray(item.hall_aliases_latex) ? item.hall_aliases_latex.join(" ") : item.hall_aliases_latex,
      Array.isArray(item.hall_aliases_html) ? item.hall_aliases_html.join(" ") : item.hall_aliases_html,
      Array.isArray(item.hall_aliases_unicode) ? item.hall_aliases_unicode.join(" ") : item.hall_aliases_unicode,
      item.hm_entry,
      Array.isArray(item.hm_entry_aliases) ? item.hm_entry_aliases.join(" ") : item.hm_entry_aliases,
      item.hm_entry_latex,
      item.hm_entry_html,
      item.hm_entry_unicode,
      item.hm_short,
      Array.isArray(item.hm_short_aliases) ? item.hm_short_aliases.join(" ") : item.hm_short_aliases,
      Array.isArray(item.hm_short_aliases_latex) ? item.hm_short_aliases_latex.join(" ") : item.hm_short_aliases_latex,
      Array.isArray(item.hm_short_aliases_html) ? item.hm_short_aliases_html.join(" ") : item.hm_short_aliases_html,
      Array.isArray(item.hm_short_aliases_unicode) ? item.hm_short_aliases_unicode.join(" ") : item.hm_short_aliases_unicode,
      item.hm_short_latex,
      item.hm_short_html,
      item.hm_short_unicode,
      item.hm_full,
      item.hm_full_latex,
      item.hm_full_html,
      item.hm_full_unicode,
      item.hm_extended,
      item.hm_extended_latex,
      item.hm_extended_html,
      item.hm_extended_unicode,
      item.hm_universal,
      Array.isArray(item.hm_universal_aliases) ? item.hm_universal_aliases.join(" ") : item.hm_universal_aliases,
      Array.isArray(item.hm_universal_aliases_latex)
        ? item.hm_universal_aliases_latex.join(" ")
        : item.hm_universal_aliases_latex,
      Array.isArray(item.hm_universal_aliases_html)
        ? item.hm_universal_aliases_html.join(" ")
        : item.hm_universal_aliases_html,
      Array.isArray(item.hm_universal_aliases_unicode)
        ? item.hm_universal_aliases_unicode.join(" ")
        : item.hm_universal_aliases_unicode,
      item.hm_universal_latex,
      item.hm_universal_html,
      item.hm_universal_unicode,
      item.short_hm_symbol,
      item.short_hm_symbol_latex,
      item.short_hm_symbol_unicode,
      Array.isArray(item.short_hm_symbol_aliases) ? item.short_hm_symbol_aliases.join(" ") : item.short_hm_symbol_aliases,
      Array.isArray(item.short_hm_symbol_aliases_latex)
        ? item.short_hm_symbol_aliases_latex.join(" ")
        : item.short_hm_symbol_aliases_latex,
      item.universal_hm,
      item.universal_hm_latex,
      item.universal_hm_unicode,
      item.ita_number,
      Array.isArray(item.n_c) ? item.n_c.join(" ") : item.n_c,
      item.setting_it_nc,
      getArrayValues(item.n_c_aliases).join(" "),
      item.it_coordinate_system_code,
      item.crystal_system,
      item.point_group,
      item.bravais_type,
      item.centring_type
    ]
      .map((value) => String(value ?? ""))
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });
};

const filterPointgroupRows = (rows, query) => {
  const q = String(query || "").trim().toLowerCase();
  if (!q) {
    return rows;
  }

  return rows.filter((item) => {
    const haystack = [
      item.pointgroup_key,
      item.hm_symbol,
      item.schoenflies,
      item.schoenflies_html,
      item.schoenflies_unicode,
      item.schoenflies_latex,
      item.crystal_system,
      item.laue_class,
      item.order,
      item.n_conjugacy_classes,
      item.is_centrosymmetric ? "centrosymmetric" : "non-centrosymmetric"
    ]
      .map((value) => String(value ?? ""))
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });
};

const applyFilters = () => {
  const visibleRows = getActiveSourceRows();
  if (!tableView || !searchInput) {
    filteredRows = visibleRows;
    return;
  }

  if (activeDataset === DATASET_POINTGROUPS) {
    filteredRows = filterPointgroupRows(visibleRows, searchInput.value);
    return;
  }
  filteredRows = filterSpacegroupRows(visibleRows, searchInput.value);
};

const updateSummary = () => {
  if (!searchSummary) {
    return;
  }
  const config = getActiveTableConfig();
  const query = searchInput ? searchInput.value.trim() : "";
  if (!query) {
    searchSummary.textContent = `Showing all ${config.emptyLabel}`;
    return;
  }
  searchSummary.textContent = `Query "${query}" returned ${filteredRows.length} result${filteredRows.length === 1 ? "" : "s"}`;
};

const renderTableHeader = () => {
  if (!tableHead) {
    return;
  }
  const config = getActiveTableConfig();
  tableHead.innerHTML = `<tr>${config.columns
    .map((column) => {
      const labelHtml = column.docUrl
        ? `<a class="field-doc-link table-doc-link" href="${escapeHtml(column.docUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(column.label)}</a>`
        : escapeHtml(column.label);
      return `<th><div class="table-head-controls">${labelHtml}<button class="sort-btn table-sort-btn" data-sort="${column.key}" aria-label="Sort by ${escapeHtml(column.label)}">sort</button></div></th>`;
    })
    .join("")}</tr>`;
};

const renderTable = () => {
  if (!tableBody || !emptyState) {
    return;
  }

  const config = getActiveTableConfig();
  renderTableHeader();

  if (indexTable) {
    indexTable.setAttribute("aria-label", config.ariaLabel);
  }

  const baseUrl = resolveBase();
  const rows = sortRows(filteredRows);
  tableBody.innerHTML = rows
    .map((row) => {
      const rowUrl = config.rowUrl(baseUrl, row);
      const cells = config.columns
        .map((column) => {
          const className = column.muted ? ' class="td-muted"' : "";
          return `<td${className}>${column.render(row)}</td>`;
        })
        .join("");
      return `<tr class="sg-row" data-active="false" data-row-url="${escapeHtml(rowUrl)}">${cells}</tr>`;
    })
    .join("");

  emptyState.hidden = rows.length > 0;
  emptyState.textContent = `No matching ${config.emptyLabel} found.`;
  updateSummary();

  if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
    tableBody.classList.add("math-pending");
    window.MathJax.typesetPromise([tableHead || tableBody, tableBody])
      .catch((err) => {
        console.warn("MathJax typeset failed", err);
      })
      .finally(() => {
        tableBody.classList.remove("math-pending");
      });
  }
};

const updateSearchUi = () => {
  if (!tableView) {
    return;
  }
  const config = getActiveTableConfig();
  if (searchInput) {
    searchInput.placeholder = config.searchPlaceholder;
  }
};

const updateSettingsButtons = () => {
  document.querySelectorAll("[data-settings-toggle]").forEach((button) => {
    button.dataset.mode = settingsMode;
    button.setAttribute("aria-pressed", settingsMode === SETTINGS_ITA ? "true" : "false");
    button.setAttribute(
      "title",
      settingsMode === SETTINGS_ITA ? "Settings mode: ITA reference only" : "Settings mode: all"
    );
  });
};

const updateThemeButtons = () => {
  document.querySelectorAll("[data-theme-option]").forEach((button) => {
    const option = normalizeThemeMode(button.getAttribute("data-theme-option"));
    const isActive = Boolean(option) && option === themeMode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
};

const updateIndexControlVisibility = () => {
  if (!tableView) {
    return;
  }
  if (settingsToggleWrapIndex) {
    settingsToggleWrapIndex.hidden = false;
  }
};

const updateDetailSecondaryKicker = () => {
  const isAllMode = settingsMode === SETTINGS_ALL;
  document.querySelectorAll("[data-detail-secondary-kicker]").forEach((label) => {
    label.textContent = isAllMode ? "n:c" : "IT#";
  });
};

const updateSettingsConditionalVisibility = () => {
  document.querySelectorAll("[data-hide-when-settings]").forEach((section) => {
    const targetMode = normalizeSettingsMode(section.getAttribute("data-hide-when-settings"));
    if (!targetMode) {
      return;
    }
    const shouldHide = settingsMode === targetMode;
    section.hidden = shouldHide;
    section.style.display = shouldHide ? "none" : "";
  });
};

const updateSectionToggles = () => {
  document.querySelectorAll("[data-section-toggle]").forEach((button) => {
    const key = button.getAttribute("data-section-toggle");
    if (!key || !(key in sectionState)) {
      return;
    }
    const isOpen = Boolean(sectionState[key]);
    button.textContent = isOpen ? TRIANGLE_OPEN : TRIANGLE_CLOSED;
    button.setAttribute("aria-expanded", isOpen ? "true" : "false");
    button.setAttribute("aria-label", isOpen ? "Collapse section" : "Expand section");
  });

  document.querySelectorAll("[data-section-body]").forEach((body) => {
    const key = body.getAttribute("data-section-body");
    if (!key || !(key in sectionState)) {
      return;
    }
    body.hidden = !sectionState[key];
  });
};

const updateStaticHallLinks = () => {
  document.querySelectorAll("a.related-link[href], a.mapping-tab-external-link[href]").forEach((anchor) => {
    const href = anchor.getAttribute("href");
    if (!href) {
      return;
    }

    let parsed;
    try {
      parsed = new URL(href, window.location.origin);
    } catch {
      return;
    }

    if (!parsed.pathname.includes("/hall/")) {
      return;
    }

    if (!anchor.hasAttribute("data-original-settings-mode")) {
      anchor.setAttribute("data-original-settings-mode", normalizeSettingsMode(parsed.searchParams.get(SETTINGS_QUERY_KEY)) || "");
    }
    const mode = normalizeSettingsMode(anchor.getAttribute("data-original-settings-mode")) || settingsMode;
    anchor.setAttribute("href", withNavigationQuery(parsed.pathname, mode));
  });
};

const updateStaticPointgroupLinks = () => {
  document.querySelectorAll("a.related-link[href], a.inline-detail-link[href]").forEach((anchor) => {
    const href = anchor.getAttribute("href");
    if (!href) {
      return;
    }

    let parsed;
    try {
      parsed = new URL(href, window.location.origin);
    } catch {
      return;
    }

    if (!parsed.pathname.includes("/pointgroup/")) {
      return;
    }

    anchor.setAttribute("href", withNavigationQuery(parsed.pathname, settingsMode, themeMode));
  });
};

const updateDatasetTabLinks = () => {
  document.querySelectorAll("a.dataset-tab[href]").forEach((anchor) => {
    const href = anchor.getAttribute("href");
    if (!href) {
      return;
    }

    let parsed;
    try {
      parsed = new URL(href, window.location.origin);
    } catch {
      return;
    }

    anchor.setAttribute("href", withNavigationQuery(parsed.pathname, settingsMode, themeMode));
  });
};

const updateMappingVisibility = () => {
  document.querySelectorAll("[data-mapping-box]").forEach((box) => {
    const tabs = Array.from(box.querySelectorAll("[data-mapping-tab]"));
    const mappingSelect = box.querySelector("[data-mapping-select]");
    const panels = Array.from(box.querySelectorAll("[data-mapping-panel]"));
    let visiblePanelIds = [];
    let activeTargetId = box.getAttribute("data-active-target-id");

    if (tabs.length > 0) {
      const visibleTabs = tabs.filter((tab) => {
        const isReference = tab.getAttribute("data-is-reference-setting") === "true";
        const visible = settingsMode !== SETTINGS_ITA || isReference;
        const tabItem = tab.closest("[data-mapping-tab-item]");
        if (tabItem) {
          tabItem.hidden = !visible;
          tabItem.style.display = visible ? "" : "none";
        }
        tab.hidden = !visible;
        tab.style.display = visible ? "" : "none";
        return visible;
      });

      visiblePanelIds = visibleTabs.map((tab) => tab.getAttribute("data-target-id")).filter(Boolean);

      if (!activeTargetId || !visiblePanelIds.includes(activeTargetId)) {
        activeTargetId = visibleTabs.length > 0 ? visibleTabs[0].getAttribute("data-target-id") : null;
      }

      tabs.forEach((tab) => {
        const targetId = tab.getAttribute("data-target-id");
        const isActive = Boolean(targetId) && targetId === activeTargetId && !tab.hidden;
        tab.classList.toggle("is-active", isActive);
        tab.setAttribute("aria-selected", isActive ? "true" : "false");
      });
    } else if (mappingSelect instanceof HTMLSelectElement) {
      const options = Array.from(mappingSelect.options);
      const visibleOptions = options.filter((option) => {
        const isReference = option.getAttribute("data-is-reference-setting") === "true";
        const visible = settingsMode !== SETTINGS_ITA || isReference;
        option.hidden = !visible;
        return visible;
      });

      visiblePanelIds = visibleOptions
        .map((option) => option.getAttribute("data-target-id") || option.value)
        .filter(Boolean);

      const selectedTargetId = mappingSelect.value;
      if (!activeTargetId && visiblePanelIds.includes(selectedTargetId)) {
        activeTargetId = selectedTargetId;
      }
      if (!activeTargetId || !visiblePanelIds.includes(activeTargetId)) {
        activeTargetId = visiblePanelIds.length > 0 ? visiblePanelIds[0] : null;
      }
      if (activeTargetId) {
        mappingSelect.value = activeTargetId;
      } else {
        mappingSelect.selectedIndex = -1;
      }
    }

    if (activeTargetId) {
      box.setAttribute("data-active-target-id", activeTargetId);
    } else {
      box.removeAttribute("data-active-target-id");
    }

    const visiblePanelIdSet = new Set(visiblePanelIds);

    panels.forEach((panel) => {
      const panelId = panel.getAttribute("id");
      const isReference = panel.getAttribute("data-is-reference-setting") === "true";
      const allowedByMode = settingsMode !== SETTINGS_ITA || isReference;
      const isVisiblePanel = Boolean(panelId) && panelId === activeTargetId && visiblePanelIdSet.has(panelId) && allowedByMode;
      panel.hidden = !isVisiblePanel;
      panel.style.display = isVisiblePanel ? "" : "none";
    });

    const emptyNote = box.querySelector("[data-mapping-empty]");
    if (emptyNote) {
      emptyNote.hidden = !(settingsMode === SETTINGS_ITA && visiblePanelIds.length === 0);
    }
  });
};

const updateBackButtonHref = () => {
  const backButton = document.querySelector(".header-back-btn");
  if (!backButton) {
    return;
  }
  backButton.setAttribute("href", buildRootUrl(resolveBase(), settingsMode, activeDataset));
};

const getCurrentDetailHallKey = () => {
  const hallSelect = document.querySelector('select.detail-select[data-selected][aria-label="Select Hall symbol"]');
  if (!hallSelect) {
    return null;
  }

  const selectedFromData = hallSelect.dataset.selected;
  if (selectedFromData) {
    return selectedFromData;
  }

  const selectedOption = hallSelect.options[hallSelect.selectedIndex];
  if (selectedOption && selectedOption.dataset.matchValue) {
    return selectedOption.dataset.matchValue;
  }

  return null;
};

const maybeRedirectToItaReferenceSetting = () => {
  const currentHallKey = getCurrentDetailHallKey();
  if (!currentHallKey) {
    return false;
  }

  const current = allRows.find((row) => row.hall_key === currentHallKey);
  if (!current || current.is_reference_setting) {
    return false;
  }

  if (current.ita_number === null || current.ita_number === undefined) {
    return false;
  }

  const siblings = allRows.filter((row) => row.ita_number === current.ita_number);
  const standard = chooseStandardSetting(siblings);
  if (!standard || standard.hall_key === currentHallKey) {
    return false;
  }

  window.location.assign(buildHallUrl(resolveBase(), standard.hall_key, SETTINGS_ITA));
  return true;
};

const setupEvents = () => {
  if (searchInput) {
    let debounceTimer = null;
    searchInput.addEventListener("input", () => {
      window.clearTimeout(debounceTimer);
      debounceTimer = window.setTimeout(() => {
        applyFilters();
        renderTable();
      }, 220);
    });
  }

  document.querySelectorAll("[data-section-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.getAttribute("data-section-toggle");
      if (!key || !(key in sectionState)) {
        return;
      }

      sectionState[key] = !sectionState[key];
      syncModeUrlAndStorage();
      updateSectionToggles();
      refreshUiState();
    });
  });

  document.querySelectorAll("[data-mapping-tab]").forEach((tab) => {
    tab.addEventListener("click", () => {
      const box = tab.closest("[data-mapping-box]");
      const targetId = tab.getAttribute("data-target-id");
      if (!box || !targetId || tab.hidden) {
        return;
      }
      box.setAttribute("data-active-target-id", targetId);
      updateMappingVisibility();
    });
  });

  document.querySelectorAll("[data-mapping-select]").forEach((select) => {
    select.addEventListener("change", () => {
      const box = select.closest("[data-mapping-box]");
      if (!box) {
        return;
      }
      const targetId = select.value;
      if (!targetId) {
        return;
      }
      box.setAttribute("data-active-target-id", targetId);
      updateMappingVisibility();
    });
  });

  if (tableBody) {
    tableBody.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      if (target.closest("a, button, input, select, textarea, label")) {
        return;
      }

      const row = target.closest("tr[data-row-url]");
      if (!row) {
        return;
      }
      const rowUrl = row.getAttribute("data-row-url");
      if (rowUrl) {
        window.location.assign(rowUrl);
      }
    });
  }

  if (tableView) {
    tableView.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      const button = target.closest(".sort-btn");
      if (!button) {
        return;
      }
      const key = button.getAttribute("data-sort");
      if (!key) {
        return;
      }

      if (sortState.key === key) {
        sortState.direction = sortState.direction === "asc" ? "desc" : "asc";
      } else {
        sortState.key = key;
        sortState.direction = "asc";
      }

      renderTable();
    });
  }

  document.querySelectorAll("[data-settings-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      settingsMode = settingsMode === SETTINGS_ITA ? SETTINGS_ALL : SETTINGS_ITA;
      syncModeUrlAndStorage();
      if (settingsMode === SETTINGS_ITA && maybeRedirectToItaReferenceSetting()) {
        return;
      }
      refreshUiState();
    });
  });

  document.querySelectorAll("[data-theme-option]").forEach((button) => {
    button.addEventListener("click", () => {
      const option = normalizeThemeMode(button.getAttribute("data-theme-option"));
      if (!option || option === themeMode) {
        return;
      }
      themeMode = option;
      syncModeUrlAndStorage();
      refreshUiState();
    });
  });

};

const chooseStandardSetting = (entries) => {
  if (!entries.length) {
    return null;
  }
  const standard = entries.find((entry) => entry.is_reference_setting);
  return standard || entries[0];
};

const buildIndexRows = (data) => {
  if (data && typeof data === "object" && data.data && Array.isArray(data.data.spacegroups)) {
    const rows = [];
    const index = data.indicies && data.indicies.index_hall_entry_to_spacegroups;
    if (index && typeof index === "object") {
      Object.entries(index)
        .sort((a, b) => (Number(a[1]) || 0) - (Number(b[1]) || 0))
        .forEach(([hallKey, pos]) => {
          const entry = data.data.spacegroups[pos];
          if (entry && typeof entry === "object") {
            rows.push(normalizeRow({ ...entry, hall_key: hallKey }));
          }
        });
    } else {
      data.data.spacegroups.forEach((entry, idx) => {
        if (entry && typeof entry === "object") {
          rows.push(normalizeRow({ ...entry, hall_key: entry.hall_entry || entry.hall || String(idx) }));
        }
      });
    }
    return rows.sort((a, b) => {
      const itaA = a.ita_number ?? 0;
      const itaB = b.ita_number ?? 0;
      if (itaA !== itaB) {
        return itaA - itaB;
      }
      return String(a.hall_key).localeCompare(String(b.hall_key), undefined, { numeric: true });
    });
  }

  const rows = Object.entries(data).map(([hallKey, entry]) => {
    const row = { hall_key: hallKey };
    INDEX_FIELDS.forEach((field) => {
      if (field === "hall_key") {
        return;
      }
      row[field] = entry[field] ?? null;
    });
    return row;
  });

  return rows.sort((a, b) => {
    const itaA = a.ita_number ?? 0;
    const itaB = b.ita_number ?? 0;
    if (itaA !== itaB) {
      return itaA - itaB;
    }
    return String(a.hall_key).localeCompare(String(b.hall_key));
  });
};

const buildPointgroupRows = (data) => {
  let rows = [];

  if (data && typeof data === "object" && data.data && Array.isArray(data.data.pointgroups)) {
    rows = data.data.pointgroups.map((row) => normalizePointgroupRow(row));
  } else if (Array.isArray(data)) {
    rows = data.map((row) => normalizePointgroupRow(row));
  } else if (data && typeof data === "object") {
    rows = Object.entries(data).map(([pointgroupKey, entry]) => {
      const rawEntry = entry && typeof entry === "object" ? entry : {};
      return normalizePointgroupRow({
        ...rawEntry,
        pointgroup_key: pointgroupKey,
        hm_symbol: rawEntry.hm_symbol ?? pointgroupKey
      });
    });
  }

  // Ensure every row has a unique slug, even when we loaded fallback raw basics.
  const usedSlugs = new Set();
  rows.forEach((row) => {
    const base = firstNonEmpty(row.slug, slugifyPointgroupSymbol(row.hm_symbol || row.pointgroup_key));
    let slug = String(base);
    let suffix = 2;
    while (usedSlugs.has(slug)) {
      slug = `${base}-${suffix}`;
      suffix += 1;
    }
    usedSlugs.add(slug);
    row.slug = slug;
  });

  rows.sort((a, b) => {
    const cs = String(a.crystal_system || "").localeCompare(String(b.crystal_system || ""));
    if (cs !== 0) {
      return cs;
    }
    const orderA = a.order ?? 10 ** 9;
    const orderB = b.order ?? 10 ** 9;
    if (orderA !== orderB) {
      return orderA - orderB;
    }
    return String(a.hm_symbol || a.pointgroup_key || "").localeCompare(String(b.hm_symbol || b.pointgroup_key || ""));
  });

  return rows;
};

const buildLists = (rows) => {
  const hmGroups = new Map();
  const itaGroups = new Map();
  const ncGroups = new Map();
  const hmValues = new Set();
  const itaValues = new Set();
  const hallOptions = [];
  const hmOptions = [];

  const hmOptionBaseLabel = (row, fallback = "") =>
    normalizeDropdownSymbolLabel(String(firstNonEmpty(row.hm_short_unicode, fallback) || ""));
  const hallOptionBaseLabel = (row, fallback = "") =>
    normalizeDropdownSymbolLabel(String(firstNonEmpty(row.hall_unicode, fallback) || ""));

  rows.forEach((row) => {
    const hallKey = String(row.hall_key || "");
    const hallLabel = hallOptionBaseLabel(row, hallKey);
    if (hallKey) {
      hallOptions.push({
        matchValue: hallKey,
        hallKey,
        label: hallLabel,
        itaNumber: row.ita_number
      });
    }

    if (row.hm_short || row.short_hm_symbol || row.hm_short_unicode || row.hm_short_html) {
      const key = hmOptionBaseLabel(row);
      if (key) {
        hmValues.add(key);
        if (!hmGroups.has(key)) {
          hmGroups.set(key, []);
        }
        hmGroups.get(key).push(row);

        const hmDisplay = hmOptionBaseLabel(row, key);
        hmOptions.push({
          matchValue: key,
          hallKey,
          label: hmDisplay,
          itaNumber: row.ita_number
        });
      }
    }
    if (row.ita_number !== null && row.ita_number !== undefined) {
      const key = Number(row.ita_number);
      itaValues.add(key);
      if (!itaGroups.has(key)) {
        itaGroups.set(key, []);
      }
      itaGroups.get(key).push(row);
    }
    [row.n_c, ...getArrayValues(row.n_c_aliases)].forEach((nc) => {
      if (nc === null || nc === undefined || String(nc).trim() === "") {
        return;
      }
      const key = Array.isArray(nc) ? nc.join(", ") : String(nc);
      if (!ncGroups.has(key)) {
        ncGroups.set(key, []);
      }
      ncGroups.get(key).push(row);
    });
  });

  const hmToHall = {};
  const hmDisplay = {};
  const hmSortRows = {};
  hmGroups.forEach((entries, hm) => {
    const selected = chooseStandardSetting(entries);
    if (selected) {
      hmToHall[hm] = selected.hall_key;
      hmDisplay[hm] = hmOptionBaseLabel(selected, hm);
      hmSortRows[hm] = selected;
    }
  });

  const itaToHall = {};
  itaGroups.forEach((entries, ita) => {
    const selected = chooseStandardSetting(entries);
    if (selected) {
      itaToHall[String(ita)] = selected.hall_key;
    }
  });

  const ncToHall = {};
  const ncValues = [];
  ncGroups.forEach((entries, nc) => {
    const selected = chooseStandardSetting(entries);
    if (selected) {
      ncToHall[nc] = selected.hall_key;
      ncValues.push(nc);
    }
  });

  const hmValuesSorted = Array.from(hmValues).sort((a, b) => {
    const rowA = hmSortRows[a];
    const rowB = hmSortRows[b];
    const labelA = rowA ? hmDisplay[a] : String(a);
    const labelB = rowB ? hmDisplay[b] : String(b);
    return String(labelA).localeCompare(String(labelB), undefined, { numeric: true });
  });

  const hallOptionsSorted = hallOptions.sort((a, b) => {
    const byLabel = String(a.label).localeCompare(String(b.label), undefined, { numeric: true });
    if (byLabel !== 0) {
      return byLabel;
    }
    return String(a.hallKey).localeCompare(String(b.hallKey), undefined, { numeric: true });
  });
  const hmOptionsSorted = hmOptions.sort((a, b) => {
    const byLabel = String(a.label).localeCompare(String(b.label), undefined, { numeric: true });
    if (byLabel !== 0) {
      return byLabel;
    }
    return String(a.hallKey).localeCompare(String(b.hallKey), undefined, { numeric: true });
  });

  return {
    halls: hallOptionsSorted,
    hmOptions: hmOptionsSorted,
    hmValues: hmValuesSorted,
    itaValues: Array.from(itaValues).sort((a, b) => a - b),
    ncValues: ncValues.sort((a, b) => String(a).localeCompare(String(b), undefined, { numeric: true })),
    hmToHall,
    hmDisplay,
    itaToHall,
    ncToHall
  };
};

const populateSelect = (select, items, selectedValue, buildOption) => {
  if (!select) {
    return;
  }
  select.innerHTML = "";
  items.forEach((item) => {
    const option = buildOption(item);
    if (selectedValue !== null && selectedValue !== undefined) {
      if (String(option.dataset.matchValue) === String(selectedValue)) {
        option.selected = true;
      }
    }
    select.appendChild(option);
  });
};

const populateDetailSelects = (lists) => {
  const baseUrl = resolveBase();
  const hallSelects = document.querySelectorAll('select.detail-select[data-selected][aria-label="Select Hall symbol"]');
  const hmSelects = document.querySelectorAll('select.detail-select[data-selected][aria-label="Select HM symbol"]');
  const itaSelects = document.querySelectorAll('select.detail-select[data-secondary-select], select.detail-select[data-selected][aria-label="Select ITA number"]');

  hallSelects.forEach((select) => {
    const selected = select.dataset.selected;
    populateSelect(select, lists.halls, selected, (hallKey) => {
      const option = document.createElement("option");
      option.value = hallKey.hallKey ? buildHallUrl(baseUrl, hallKey.hallKey) : "";
      const itaSuffix =
        hallKey.itaNumber !== null && hallKey.itaNumber !== undefined ? `  -  (#${hallKey.itaNumber})` : "";
      option.textContent = `${hallKey.label}${itaSuffix}`;
      option.dataset.matchValue = hallKey.matchValue;
      return option;
    });
  });

  hmSelects.forEach((select, idx) => {
    const selected = select.dataset.selected;
    const selectedHall = (hallSelects[idx] && hallSelects[idx].dataset && hallSelects[idx].dataset.selected) || "";
    populateSelect(select, lists.hmOptions || [], selected, (hmOption) => {
      const option = document.createElement("option");
      option.value = hmOption.hallKey ? buildHallUrl(baseUrl, hmOption.hallKey) : "";
      const itaSuffix =
        hmOption.itaNumber !== null && hmOption.itaNumber !== undefined ? `  -  (#${hmOption.itaNumber})` : "";
      option.textContent = `${hmOption.label}${itaSuffix}`;
      option.dataset.matchValue = hmOption.matchValue;
      option.dataset.hallKey = hmOption.hallKey || "";
      return option;
    });

    // Prefer a stable hall-key match over symbol-text matching.
    if (selectedHall) {
      const byHall = Array.from(select.options).find((opt) => String(opt.dataset.hallKey || "") === String(selectedHall));
      if (byHall) {
        byHall.selected = true;
      }
    }
  });

  itaSelects.forEach((select) => {
    const isAllMode = settingsMode === SETTINGS_ALL;
    const selected = isAllMode ? select.dataset.selectedNc || select.dataset.selected : select.dataset.selectedIta || select.dataset.selected;
    if (isAllMode) {
      populateSelect(select, lists.ncValues || [], selected, (nc) => {
        const hall = lists.ncToHall[String(nc)];
        const option = document.createElement("option");
        option.value = hall ? buildHallUrl(baseUrl, hall) : "";
        option.textContent = String(nc);
        option.dataset.matchValue = String(nc);
        return option;
      });
      return;
    }

    populateSelect(select, lists.itaValues, selected, (ita) => {
      const hall = lists.itaToHall[String(ita)];
      const option = document.createElement("option");
      option.value = hall ? buildHallUrl(baseUrl, hall) : "";
      option.textContent = `#${ita}`;
      option.dataset.matchValue = String(ita);
      return option;
    });
  });
};

const refreshUiState = () => {
  const modeRows = getRowsForMode(allRows);
  const lists = buildLists(modeRows);
  populateDetailSelects(lists);

  if (tableView) {
    ensureSortKeyForActiveDataset();
    updateSearchUi();
    updateIndexControlVisibility();
    applyFilters();
    renderTable();
  }

  updateSettingsButtons();
  updateDetailSecondaryKicker();
  updateSettingsConditionalVisibility();
  updateThemeButtons();
  updateSectionToggles();
  updateMappingVisibility();
  updateStaticHallLinks();
  updateStaticPointgroupLinks();
  updateDatasetTabLinks();
  updateBackButtonHref();
};

const loadSpacegroupRows = async (baseUrl) => {
  const sources = [INDEX_DATA_PATH, SYMMETRY_BASICS_DATA_PATH];
  for (const source of sources) {
    try {
      const response = await fetch(`${baseUrl}${source}`, { cache: "force-cache" });
      const data = await readJsonResponse(response, source);
      if (Array.isArray(data)) {
        return normalizeRows(data);
      }
      return normalizeRows(buildIndexRows(data));
    } catch (error) {
      console.warn(`Unable to load ${source}`, error);
    }
  }
  return [];
};

const loadPointgroupRows = async (baseUrl) => {
  const sources = [POINTGROUP_INDEX_DATA_PATH, SYMMETRY_BASICS_DATA_PATH];
  for (const source of sources) {
    try {
      const response = await fetch(`${baseUrl}${source}`, { cache: "force-cache" });
      const data = await readJsonResponse(response, source);
      return buildPointgroupRows(data);
    } catch (error) {
      console.warn(`Unable to load ${source}`, error);
    }
  }
  return [];
};

const initIndex = async () => {
  const requestedMode = getModeFromUrl();
  syncModeUrlAndStorage();
  updateSettingsButtons();
  updateThemeButtons();
  updateBackButtonHref();

  const baseUrl = resolveBase();
  allRows = await loadSpacegroupRows(baseUrl);
  pointgroupRows = await loadPointgroupRows(baseUrl);

  const current = allRows.find((row) => row.hall_key === getCurrentDetailHallKey());
  if (current && !current.is_reference_setting && settingsMode === SETTINGS_ITA) {
    if (requestedMode === SETTINGS_ITA && maybeRedirectToItaReferenceSetting()) {
      return;
    }
    settingsMode = SETTINGS_ALL;
    syncModeUrlAndStorage();
  }
  setupEvents();
  refreshUiState();
};

initIndex();
