//! PII regex patterns

use regex::{Regex, RegexBuilder, RegexSet, RegexSetBuilder};
use std::sync::LazyLock;

/// Registry of cleaners and their regex patterns.
///
/// Cleaners are stored in **priority order**: specific PII types come before
/// broad catch-alls. The order is fixed so that detection and redaction are
/// deterministic, and it decides which label wins when matches from several
/// cleaners overlap.
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
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                    r"\b[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\b",
                ],
            ),
            (
                "nino",
                vec![
                    r"[A-CEGHJ-PR-TW-Z]{1}\s{0,2}[A-CEGHJ-NPR-TW-Z]{1}\s{0,2}[0-9]{2}\s{0,2}[0-9]{2}\s{0,2}[0-9]{2}(?:\s{1,2}[A-D]\b|[A-D])?",
                ],
            ),
            ("postcode", vec![r"\b[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}\b"]),
            (
                "telephone",
                vec![
                    r"(?:(?:\(?(?:0(?:0|11)\)?[\s-]?\(?|\+)44\)?[\s-]?(?:\(?0\)?[\s-]?)?)|(?:\(?0))(?:(?:\d{5,6}\)?[\s-]?\d{4,6})|(?:\d{4}\)?[\s-]?(?:\d{5,6}|\d{3,4}[\s-]?\d{3,4}))|(?:\d{3,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4})|(?:\d{2}\)?[\s-]?\d{4}[\s-]?\d{4}))(?:[\s-]?(?:x|ext\.?|\#)\d{1,4})?\b",
                ],
            ),
            (
                "ip_address",
                vec![
                    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
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
