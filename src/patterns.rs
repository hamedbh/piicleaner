//! PII regex patterns

use regex::{Regex, RegexBuilder, RegexSet, RegexSetBuilder};
use std::sync::LazyLock;

/// Registry of cleaners and their regex patterns.
///
/// Cleaners are stored in **priority order**: specific PII types come before
/// broad catch-alls. The order is fixed so that detection and redaction are
/// deterministic, and it decides which label wins when matches from several
/// cleaners overlap.
///
/// Word boundaries are ASCII-only, `(?-u:\b)`, never a plain `\b`. A Unicode
/// boundary makes the regex engine fall back to a slow search on any text
/// with a non-ASCII character, 300-450x slower for the `RegexSet`. It would
/// also stop matches next to non-ASCII letters, as in Chinese and Japanese
/// text, which has no spaces ("邮箱john@example.com谢谢").
pub struct PatternRegistry {
    patterns: Vec<(&'static str, Vec<&'static str>)>,
}

impl PatternRegistry {
    fn new() -> Self {
        let patterns = vec![
            // Two email patterns: a simple one and then a more comprehensive RFC-compliant version
            (
                "email",
                vec![
                    r"(?-u:\b)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}(?-u:\b)",
                    r"(?-u:\b)[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*(?-u:\b)",
                ],
            ),
            (
                "nino",
                vec![
                    // Up to two spaces, dashes or dots between groups, with the
                    // digits grouped 2-2-2 or 3-3. Separators are not allowed
                    // between any digits, as that matches inside phone numbers
                    // (e.g. "ca[ll 07700 9]00123"). The 3-3 form must end at a
                    // word boundary or suffix letter, so "020 794" in
                    // "020 7946 0958" isn't matched.
                    r"[A-CEGHJ-PR-TW-Z][\s\-.]{0,2}[A-CEGHJ-NPR-TW-Z][\s\-.]{0,2}(?:[0-9]{2}[\s\-.]{0,2}[0-9]{2}[\s\-.]{0,2}[0-9]{2}|[0-9]{3}[\s\-.]{0,2}[0-9]{3}(?:(?-u:\b)|[A-D]))(?:[\s\-.]{1,2}[A-D](?-u:\b)|[A-D])?",
                ],
            ),
            // Any whitespace between the outward and inward codes, including double
            // spaces, tabs and line breaks
            (
                "postcode",
                vec![r"(?-u:\b)[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}(?-u:\b)"],
            ),
            (
                "telephone",
                vec![
                    r"(?:(?:\(?(?:0(?:0|11)\)?[\s-]?\(?|\+)44\)?[\s-]?(?:\(?0\)?[\s-]?)?)|(?:\(?0))(?:(?:\d{5,6}\)?[\s-]?\d{4,6})|(?:\d{4}\)?[\s-]?(?:\d{5,6}|\d{3,4}[\s-]?\d{3,4}))|(?:\d{3,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4})|(?:\d{2}\)?[\s-]?\d{4}[\s-]?\d{4}))(?:[\s-]?(?:x|ext\.?|\#)\d{1,4})?(?-u:\b)",
                ],
            ),
            (
                "international-telephone",
                vec![
                    // A "+" or "00" prefix, a 1-3 digit country code, then
                    // 6-14 digits with an optional space, dot or hyphen
                    // between any two, and brackets between digits, as in
                    // "+1 (415) 555-0132" or "+44 (0)20 7946 0958". A ")" is
                    // only taken before another digit, so the bracket in
                    // "(+1 415 555 0132)" is left alone. Looser
                    // than E.164's 15-digit limit, so no number is missed.
                    // The country code can't start with 0, which keeps out
                    // UTC offsets such as "+01:00". Numbers without a prefix
                    // can't be told apart from UK numbers or other digit
                    // runs, so they're left to `telephone` and `case-id`.
                    // A space is allowed after the prefix ("00 33 1 ..."),
                    // which also matches "00 2024-01-15" in "10:00
                    // 2024-01-15": over-redaction is preferred to a miss
                    r"(?:\+|(?-u:\b)00)\s?[1-9][0-9]{0,2}(?:\)?[\s.\-]?\(?[0-9]){6,14}(?:\s?(?:x|ext\.?|\#)\s?[0-9]{1,5})?",
                ],
            ),
            (
                "ip_address",
                vec![
                    r"(?-u:\b)(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?-u:\b)",
                    // IPv6: the full 8-group form, the "::" compressed forms and
                    // forms ending in an embedded IPv4 address, with an optional
                    // zone ID. Looser than the RFC (it doesn't count the groups
                    // either side of "::") so no valid address is missed. Each
                    // form must start and end at a word boundary, which stops a
                    // match ending partway through an address and keeps it out
                    // of "HH:MM:SS" times and code such as "crate::fmt". The
                    // boundaries are ASCII-only, which is measurably faster and
                    // also matches an address directly after a non-ASCII letter
                    r"(?:(?-u:\b)(?:[0-9A-Fa-f]{1,4}:){6}(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?-u:\b)|(?-u:\b)(?:[0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}(?-u:\b)|(?:(?-u:\b)[0-9A-Fa-f]{1,4}(?::[0-9A-Fa-f]{1,4}){0,6}|(?-u:\B))::(?:(?:[0-9A-Fa-f]{1,4}:){0,5}(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?-u:\b)|[0-9A-Fa-f]{1,4}(?::[0-9A-Fa-f]{1,4}){0,6}(?-u:\b)|(?-u:\B)))(?:%[0-9A-Za-z._~-]+)?",
                ],
            ),
            (
                "address",
                vec![r"\d{1,3} \w{3,} (street|lane|road|close|avenue|drive|grove|mansions|way)"],
            ),
            ("tag", vec![r"<.*script.*>", r"<.*>"]),
            (
                "cash-amount",
                vec![
                    r"(([£€$]{1}|GBP|USD|EUR)\s?)[\d,.]{2,}",
                    r"[\d\,\.]{2,}(\s?(GBP|USD|EUR)){1}",
                ],
            ),
            (
                "case-id",
                vec![
                    r"[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}",
                    r"(ref|reference)(\snumber)?\s?[:\-#]?\s?\w{0,3}\s?[#.a-f0-9]{6,}",
                    r"asm\s?\d{18,}",
                    r"[a-f0-9]{8,}",
                    r"\d{6,}",
                ],
            ),
        ];

        Self { patterns }
    }

    pub fn get_all_patterns(&self) -> Vec<&'static str> {
        self.patterns
            .iter()
            .flat_map(|(_, patterns)| patterns.iter().copied())
            .collect()
    }

    pub fn get_patterns_by_name(&self, cleaners: &[&str]) -> Vec<&'static str> {
        cleaners
            .iter()
            .filter_map(|&cleaner| {
                self.patterns
                    .iter()
                    .find(|(name, _)| *name == cleaner)
                    .map(|(_, patterns)| patterns)
            })
            .flatten()
            .copied()
            .collect()
    }

    /// Cleaner names in priority order.
    pub fn get_available_cleaners(&self) -> Vec<&'static str> {
        self.patterns.iter().map(|(name, _)| *name).collect()
    }
}

// Create a static instance
pub fn get_registry() -> &'static PatternRegistry {
    use std::sync::OnceLock;
    static REGISTRY: OnceLock<PatternRegistry> = OnceLock::new();
    REGISTRY.get_or_init(PatternRegistry::new)
}

pub fn get_all_patterns() -> Vec<&'static str> {
    get_registry().get_all_patterns()
}

pub fn get_patterns_by_name(cleaners: &[&str]) -> Vec<&'static str> {
    get_registry().get_patterns_by_name(cleaners)
}

/// A cleaner with its compiled regexes and redaction label.
pub struct CompiledCleaner {
    pub name: &'static str,
    /// Position in the registry; lower values take precedence.
    pub priority: usize,
    pub regexes: Vec<Regex>,
    pub replacement: String,
}

fn compile_cleaners(ignore_case: bool) -> Vec<CompiledCleaner> {
    get_registry()
        .patterns
        .iter()
        .enumerate()
        .map(|(priority, (name, patterns))| CompiledCleaner {
            name,
            priority,
            regexes: patterns
                .iter()
                .map(|p| {
                    RegexBuilder::new(p)
                        .case_insensitive(ignore_case)
                        .build()
                        .expect("Invalid regex")
                })
                .collect(),
            replacement: format!("[{}-redacted]", name),
        })
        .collect()
}

pub static CLEANERS_CASE_SENSITIVE: LazyLock<Vec<CompiledCleaner>> =
    LazyLock::new(|| compile_cleaners(false));

pub static CLEANERS_CASE_INSENSITIVE: LazyLock<Vec<CompiledCleaner>> =
    LazyLock::new(|| compile_cleaners(true));

pub static PATTERNS_SET_CASE_SENSITIVE: LazyLock<RegexSet> = LazyLock::new(|| {
    let pattern_strings = get_all_patterns();
    RegexSet::new(pattern_strings).expect("Failed to create regex set")
});

pub static PATTERNS_SET_CASE_INSENSITIVE: LazyLock<RegexSet> = LazyLock::new(|| {
    let pattern_strings = get_all_patterns();
    RegexSetBuilder::new(pattern_strings)
        .case_insensitive(true)
        .build()
        .expect("Failed to create case-insensitive regex set")
});

#[inline]
pub fn get_patterns(ignore_case: bool) -> (&'static [CompiledCleaner], &'static RegexSet) {
    if ignore_case {
        (&CLEANERS_CASE_INSENSITIVE, &PATTERNS_SET_CASE_INSENSITIVE)
    } else {
        (&CLEANERS_CASE_SENSITIVE, &PATTERNS_SET_CASE_SENSITIVE)
    }
}
