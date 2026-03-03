/**
 * romaji.ts — Smart Japanese search utility for DailyFluent.
 *
 * Features:
 * 1. Romaji → Hiragana conversion (Hepburn + Kunrei-shiki + Nihon-shiki)
 * 2. Hiragana ↔ Katakana interconversion
 * 3. Vietnamese diacritics normalization (fuzzy Han Viet matching)
 * 4. Multi-word query support (every word must match at least one field)
 * 5. Partial romaji handling (typing "kin" matches "きん止")
 * 6. Double consonants, standalone ん, combo kana
 */

// ── Romaji → Hiragana table ──
// Sorted longest-first for greedy matching.
const ROMAJI_TO_HIRAGANA: [string, string][] = [
  // 4-char
  ["xtsu", "っ"], ["ltsu", "っ"],
  ["shya", "しゃ"], ["shyu", "しゅ"], ["shyo", "しょ"],
  ["chya", "ちゃ"], ["chyu", "ちゅ"], ["chyo", "ちょ"],
  // 3-char combos
  ["sha", "しゃ"], ["shi", "し"], ["sho", "しょ"], ["shu", "しゅ"], ["she", "しぇ"],
  ["chi", "ち"], ["cha", "ちゃ"], ["cho", "ちょ"], ["chu", "ちゅ"], ["che", "ちぇ"],
  ["tsu", "つ"], ["tsa", "つぁ"], ["tsi", "つぃ"], ["tse", "つぇ"], ["tso", "つぉ"],
  ["cya", "ちゃ"], ["cyi", "ち"], ["cyu", "ちゅ"], ["cye", "ちぇ"], ["cyo", "ちょ"],
  ["dya", "ぢゃ"], ["dyi", "ぢぃ"], ["dyu", "ぢゅ"], ["dye", "ぢぇ"], ["dyo", "ぢょ"],
  ["nya", "にゃ"], ["nyi", "にぃ"], ["nyu", "にゅ"], ["nye", "にぇ"], ["nyo", "にょ"],
  ["hya", "ひゃ"], ["hyi", "ひぃ"], ["hyu", "ひゅ"], ["hye", "ひぇ"], ["hyo", "ひょ"],
  ["mya", "みゃ"], ["myi", "みぃ"], ["myu", "みゅ"], ["mye", "みぇ"], ["myo", "みょ"],
  ["rya", "りゃ"], ["ryi", "りぃ"], ["ryu", "りゅ"], ["rye", "りぇ"], ["ryo", "りょ"],
  ["gya", "ぎゃ"], ["gyi", "ぎぃ"], ["gyu", "ぎゅ"], ["gye", "ぎぇ"], ["gyo", "ぎょ"],
  ["bya", "びゃ"], ["byi", "びぃ"], ["byu", "びゅ"], ["bye", "びぇ"], ["byo", "びょ"],
  ["pya", "ぴゃ"], ["pyi", "ぴぃ"], ["pyu", "ぴゅ"], ["pye", "ぴぇ"], ["pyo", "ぴょ"],
  ["kya", "きゃ"], ["kyi", "きぃ"], ["kyu", "きゅ"], ["kye", "きぇ"], ["kyo", "きょ"],
  ["jya", "じゃ"], ["jyu", "じゅ"], ["jyo", "じょ"],
  ["tya", "ちゃ"], ["tyi", "ちぃ"], ["tyu", "ちゅ"], ["tye", "ちぇ"], ["tyo", "ちょ"],
  ["sya", "しゃ"], ["syi", "しぃ"], ["syu", "しゅ"], ["sye", "しぇ"], ["syo", "しょ"],
  ["zya", "じゃ"], ["zyi", "じぃ"], ["zyu", "じゅ"], ["zye", "じぇ"], ["zyo", "じょ"],
  ["dha", "でゃ"], ["dhi", "でぃ"], ["dhu", "でゅ"], ["dhe", "でぇ"], ["dho", "でょ"],
  ["tha", "てゃ"], ["thi", "てぃ"], ["thu", "てゅ"], ["the", "てぇ"], ["tho", "てょ"],
  // 2-char
  ["ka", "か"], ["ki", "き"], ["ku", "く"], ["ke", "け"], ["ko", "こ"],
  ["sa", "さ"], ["si", "し"], ["su", "す"], ["se", "せ"], ["so", "そ"],
  ["ta", "た"], ["ti", "ち"], ["tu", "つ"], ["te", "て"], ["to", "と"],
  ["na", "な"], ["ni", "に"], ["nu", "ぬ"], ["ne", "ね"], ["no", "の"],
  ["ha", "は"], ["hi", "ひ"], ["hu", "ふ"], ["he", "へ"], ["ho", "ほ"],
  ["ma", "ま"], ["mi", "み"], ["mu", "む"], ["me", "め"], ["mo", "も"],
  ["ya", "や"], ["yi", "い"], ["yu", "ゆ"], ["yo", "よ"],
  ["ra", "ら"], ["ri", "り"], ["ru", "る"], ["re", "れ"], ["ro", "ろ"],
  ["la", "ら"], ["li", "り"], ["lu", "る"], ["le", "れ"], ["lo", "ろ"],
  ["wa", "わ"], ["wi", "ゐ"], ["we", "ゑ"], ["wo", "を"],
  ["ga", "が"], ["gi", "ぎ"], ["gu", "ぐ"], ["ge", "げ"], ["go", "ご"],
  ["za", "ざ"], ["zi", "じ"], ["zu", "ず"], ["ze", "ぜ"], ["zo", "ぞ"],
  ["da", "だ"], ["di", "ぢ"], ["du", "づ"], ["de", "で"], ["do", "ど"],
  ["ba", "ば"], ["bi", "び"], ["bu", "ぶ"], ["be", "べ"], ["bo", "ぼ"],
  ["pa", "ぱ"], ["pi", "ぴ"], ["pu", "ぷ"], ["pe", "ぺ"], ["po", "ぽ"],
  ["fa", "ふぁ"], ["fi", "ふぃ"], ["fu", "ふ"], ["fe", "ふぇ"], ["fo", "ふぉ"],
  ["ja", "じゃ"], ["ji", "じ"], ["ju", "じゅ"], ["je", "じぇ"], ["jo", "じょ"],
  ["va", "ゔぁ"], ["vi", "ゔぃ"], ["vu", "ゔ"], ["ve", "ゔぇ"], ["vo", "ゔぉ"],
  // 1-char vowels
  ["a", "あ"], ["i", "い"], ["u", "う"], ["e", "え"], ["o", "お"],
  // n combos (explicit double-n and n-apostrophe)
  ["nn", "ん"], ["n'", "ん"], ["xn", "ん"], ["m'", "ん"],
  // Small kana
  ["xa", "ぁ"], ["xi", "ぃ"], ["xu", "ぅ"], ["xe", "ぇ"], ["xo", "ぉ"],
  ["la", "ぁ"], ["li", "ぃ"], ["lu", "ぅ"], ["le", "ぇ"], ["lo", "ぉ"],
  ["xya", "ゃ"], ["xyu", "ゅ"], ["xyo", "ょ"],
  ["xwa", "ゎ"],
];

// Double consonants that produce っ (sokuon)
const DOUBLE_CONSONANTS = new Set([
  "kk", "ss", "tt", "pp", "cc", "gg", "dd", "bb", "zz", "jj", "ff", "rr", "ww", "hh", "mm", "nn",
]);

/**
 * Convert romaji string to hiragana.
 * Handles: double consonants (kitte → きって), standalone n (sensei → せんせい),
 * combo kana (sha/chi/tsu), multiple romanization systems.
 */
export function romajiToHiragana(input: string): string {
  const src = input.toLowerCase();
  let result = "";
  let i = 0;

  while (i < src.length) {
    // Handle double consonants → っ
    if (
      i + 1 < src.length &&
      src[i] === src[i + 1] &&
      DOUBLE_CONSONANTS.has(src[i] + src[i + 1])
    ) {
      // Exception: nn → ん (don't produce っ)
      if (src[i] === "n") {
        result += "ん";
        i += 2;
        continue;
      }
      result += "っ";
      i += 1;
      continue;
    }

    // Try longest match first
    let matched = false;
    for (const [romaji, kana] of ROMAJI_TO_HIRAGANA) {
      if (src.startsWith(romaji, i)) {
        result += kana;
        i += romaji.length;
        matched = true;
        break;
      }
    }

    if (!matched) {
      // Handle standalone "n" before consonant, end of string, or non-vowel
      if (src[i] === "n") {
        const next = i + 1 < src.length ? src[i + 1] : "";
        if (!next || (!"aiueoy".includes(next) && next !== "n")) {
          result += "ん";
          i += 1;
          continue;
        }
      }
      // Handle "m" before b/p/m (e.g. "shimbun" → しんぶん)
      if (src[i] === "m" && i + 1 < src.length && "bp".includes(src[i + 1])) {
        result += "ん";
        i += 1;
        continue;
      }
      // Pass through unrecognized chars
      result += src[i];
      i += 1;
    }
  }

  return result;
}

// ── Hiragana ↔ Katakana ──
const HIRAGANA_START = 0x3041;
const HIRAGANA_END = 0x3096;
const KATAKANA_START = 0x30a1;
const KATAKANA_END = 0x30f6;
const KANA_OFFSET = 0x60;

/** Convert hiragana to katakana */
export function hiraganaToKatakana(str: string): string {
  let result = "";
  for (const ch of str) {
    const code = ch.charCodeAt(0);
    if (code >= HIRAGANA_START && code <= HIRAGANA_END) {
      result += String.fromCharCode(code + KANA_OFFSET);
    } else {
      result += ch;
    }
  }
  return result;
}

/** Convert katakana to hiragana */
export function katakanaToHiragana(str: string): string {
  let result = "";
  for (const ch of str) {
    const code = ch.charCodeAt(0);
    if (code >= KATAKANA_START && code <= KATAKANA_END) {
      result += String.fromCharCode(code - KANA_OFFSET);
    } else if (ch === "ー") {
      // Long vowel mark: keep as-is (common in katakana)
      result += ch;
    } else {
      result += ch;
    }
  }
  return result;
}

/**
 * Normalize a Japanese string: convert all katakana to hiragana.
 * This allows matching between hiragana and katakana forms.
 */
export function normalizeKana(str: string): string {
  return katakanaToHiragana(str);
}

// ── Vietnamese diacritics normalization ──
const VN_DIACRITICS: Record<string, string> = {
  "à": "a", "á": "a", "ả": "a", "ã": "a", "ạ": "a",
  "ă": "a", "ằ": "a", "ắ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a",
  "â": "a", "ầ": "a", "ấ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a",
  "è": "e", "é": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
  "ê": "e", "ề": "e", "ế": "e", "ể": "e", "ễ": "e", "ệ": "e",
  "ì": "i", "í": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
  "ò": "o", "ó": "o", "ỏ": "o", "õ": "o", "ọ": "o",
  "ô": "o", "ồ": "o", "ố": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
  "ơ": "o", "ờ": "o", "ớ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
  "ù": "u", "ú": "u", "ủ": "u", "ũ": "u", "ụ": "u",
  "ư": "u", "ừ": "u", "ứ": "u", "ử": "u", "ữ": "u", "ự": "u",
  "ỳ": "y", "ý": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
  "đ": "d",
};

/** Strip Vietnamese diacritics: "CẤM CHỈ" → "cam chi" */
export function stripVietnamese(str: string): string {
  let result = "";
  for (const ch of str.toLowerCase()) {
    result += VN_DIACRITICS[ch] || ch;
  }
  return result;
}

/** Check if a string contains Latin alphabet characters */
export function isLatin(str: string): boolean {
  return /[a-zA-Z]/.test(str);
}

/** Check if a string contains Japanese kana or kanji */
export function isJapanese(str: string): boolean {
  return /[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]/.test(str);
}

/**
 * Smart Japanese search: generate all search variant strings for a query.
 *
 * For romaji input: generates hiragana + katakana variants
 * For kana input: normalizes to hiragana for cross-kana matching
 * For all Latin input: also generates Vietnamese-stripped variant for fuzzy Han Viet matching
 *
 * Examples:
 *   "watashi"  → ["watashi", "わたし", "ワタシ"]
 *   "kin"      → ["kin", "きん", "キン"]   (partial word matching)
 *   "cam"      → ["cam"]                   (matches stripped VN: "cấm" → "cam")
 *   "禁止"     → ["禁止"]
 *   "シンブン"   → ["しんぶん", "シンブン"]  (katakana normalized to hiragana too)
 */
export function getSearchVariants(query: string): string[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const variantSet = new Set<string>();
  variantSet.add(q);

  // If input has Latin chars → generate romaji-to-kana variants
  if (isLatin(q)) {
    const hiragana = romajiToHiragana(q);
    if (hiragana !== q) {
      variantSet.add(hiragana);
      variantSet.add(hiraganaToKatakana(hiragana));
    }
    // Also add Vietnamese-stripped version for Han Viet matching
    const stripped = stripVietnamese(q);
    if (stripped !== q) {
      variantSet.add(stripped);
    }
  }

  // If input has Japanese chars → normalize kana
  if (isJapanese(q)) {
    const normalized = normalizeKana(q);
    if (normalized !== q) {
      variantSet.add(normalized);
    }
    // Also add katakana version
    variantSet.add(hiraganaToKatakana(normalizeKana(q)));
  }

  return Array.from(variantSet);
}

/**
 * Normalize a field for matching: lowercase + normalize kana + strip VN diacritics.
 * This creates multiple normalized forms of the field to maximize match potential.
 */
function normalizeField(field: string): string[] {
  const lower = field.toLowerCase();
  const forms = [lower];

  // Kana normalization: if field has katakana, also match via hiragana
  if (/[\u30a0-\u30ff]/.test(lower)) {
    forms.push(normalizeKana(lower));
  }

  // Vietnamese normalization: if field has VN diacritics, also match stripped
  const stripped = stripVietnamese(lower);
  if (stripped !== lower) {
    forms.push(stripped);
  }

  return forms;
}

/**
 * Smart match: check if a single search term matches any field.
 * Supports romaji → kana, kana normalization, and VN diacritic stripping.
 */
function matchTerm(term: string, fieldForms: string[][]): boolean {
  const variants = getSearchVariants(term);
  if (variants.length === 0) return true;

  return fieldForms.some((forms) =>
    forms.some((f) => variants.some((v) => f.includes(v)))
  );
}

/**
 * Smart match: check if a query matches against item fields.
 *
 * Features:
 * - Romaji → Hiragana/Katakana auto-conversion
 * - Vietnamese diacritics stripping (fuzzy Han Viet match)
 * - Katakana ↔ Hiragana normalization
 * - Multi-word queries: ALL words must match (AND logic)
 * - Each word can match in ANY field (OR across fields)
 *
 * @param query - User's search input (can be romaji, kana, kanji, Vietnamese)
 * @param fields - Array of strings to search against
 * @returns true if the query matches the fields
 *
 * @example
 * // Romaji search
 * smartMatch("watashi", ["私", "わたし", "", "tôi"]) // true: "わたし" matches reading
 *
 * // Vietnamese fuzzy search
 * smartMatch("cam", ["禁止", "きんし", "CẤM CHỈ", "cấm"]) // true: "cam" matches stripped "CẤM"
 *
 * // Multi-word search
 * smartMatch("cam chi", ["禁止", "きんし", "CẤM CHỈ", "cấm, ngưng"]) // true: both words match
 *
 * // Partial romaji
 * smartMatch("kin", ["禁止", "きんし", "", ""]) // true: "きん" is in "きんし"
 */
export function smartMatch(query: string, fields: string[]): boolean {
  const q = query.trim();
  if (!q) return true;

  // Pre-normalize all fields once
  const fieldForms = fields.map((f) => (f ? normalizeField(f) : [f || ""]));

  // Split query into words — ALL words must match at least one field
  const words = q.split(/\s+/).filter(Boolean);

  return words.every((word) => matchTerm(word, fieldForms));
}
