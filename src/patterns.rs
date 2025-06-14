//! PII regex patterns

use once_cell::sync::Lazy;
use regex::{Regex, RegexBuilder, RegexSet, RegexSetBuilder};
use std::collections::HashMap;

pub struct PatternRegistry {
    patterns: HashMap<&'static str, Vec<&'static str>>,
}

impl PatternRegistry {
    fn new() -> Self {
        let mut patterns = HashMap::new();

        patterns.insert(
            "cash-amount",
            vec![
                r"(([£€$]{1}|GBP|USD|EUR)\s?)[\d,.]{2,}",
                r"[\d\,\.]{2,}(\s?(GBP|USD|EUR)){1}",
            ],
        );

        patterns.insert(
            "address",
            vec![r"\d{1,3} \w{3,} (street|lane|road|close|avenue|drive|grove|mansions|way)"],
        );

        patterns.insert(
            "case-id",
            vec![
                r"[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}",
                r"(ref|reference)(\snumber)?\s?[:\-#]?\s?\w{0,3}\s?[#.a-f0-9]{6,}",
                r"asm\s?\d{18,}",
                r"[a-f0-9]{8,}",
                r"\d{6,}",
            ],
        );

        patterns.insert("nino", vec![
            r"[A-CEGHJ-PR-TW-Z]{1}\s{0,2}[A-CEGHJ-NPR-TW-Z]{1}\s{0,2}[0-9]{2}\s{0,2}[0-9]{2}\s{0,2}[0-9]{2}\s{0,2}[A-D]{0,1}",
        ]);

        patterns.insert("postcode", vec![r"\b[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}\b"]);

        patterns.insert("tag", vec![r"<.*script.*>", r"<.*>"]);

        patterns.insert("telephone", vec![
            r"(?:(?:\(?(?:0(?:0|11)\)?[\s-]?\(?|\+)44\)?[\s-]?(?:\(?0\)?[\s-]?)?)|(?:\(?0))(?:(?:\d{5,6}\)?[\s-]?\d{4,6})|(?:\d{4}\)?[\s-]?(?:\d{5,6}|\d{3,4}[\s-]?\d{3,4}))|(?:\d{3,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4})|(?:\d{2}\)?[\s-]?\d{4}[\s-]?\d{4}))(?:[\s-]?(?:x|ext\.?|\#)\d{1,4})?\b",
        ]);

        // Two email patterns: a simple one and then a more comprehensive RFC-compliant version
        patterns.insert("email", vec![
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            r"\b[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\b",
        ]);

        patterns.insert("ip_address", vec![
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
        ]);

        Self { patterns }
    }

    pub fn get_all_patterns(&self) -> Vec<&'static str> {
        self.patterns.values().flatten().copied().collect()
    }

    pub fn get_patterns_by_name(&self, cleaners: &[&str]) -> Vec<&'static str> {
        cleaners
            .iter()
            .filter_map(|&cleaner| self.patterns.get(cleaner))
            .flatten()
            .copied()
            .collect()
    }

    pub fn get_available_cleaners(&self) -> Vec<&'static str> {
        self.patterns.keys().copied().collect()
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

pub static PATTERNS_COMPILED_CASE_SENSITIVE: Lazy<HashMap<&str, Vec<Regex>>> = Lazy::new(|| {
    let registry = get_registry();
    let mut map = HashMap::new();

    for cleaner_name in registry.get_available_cleaners() {
        let patterns = registry.get_patterns_by_name(&[cleaner_name]);
        let compiled: Vec<Regex> = patterns
            .into_iter()
            .map(|p| Regex::new(p).expect("Invalid regex"))
            .collect();
        map.insert(cleaner_name, compiled);
    }
    map
});

pub static PATTERNS_COMPILED_CASE_INSENSITIVE: Lazy<HashMap<&str, Vec<Regex>>> = Lazy::new(|| {
    let registry = get_registry();
    let mut map = HashMap::new();

    for cleaner_name in registry.get_available_cleaners() {
        let patterns = registry.get_patterns_by_name(&[cleaner_name]);
        let compiled: Vec<Regex> = patterns
            .into_iter()
            .map(|p| {
                RegexBuilder::new(p)
                    .case_insensitive(true)
                    .build()
                    .expect("Invalid regex")
            })
            .collect();
        map.insert(cleaner_name, compiled);
    }
    map
});

pub static PATTERNS_SET_CASE_SENSITIVE: Lazy<RegexSet> = Lazy::new(|| {
    let pattern_strings = get_all_patterns();
    RegexSet::new(pattern_strings).expect("Failed to create regex set")
});

pub static PATTERNS_SET_CASE_INSENSITIVE: Lazy<RegexSet> = Lazy::new(|| {
    let pattern_strings = get_all_patterns();
    RegexSetBuilder::new(pattern_strings)
        .case_insensitive(true)
        .build()
        .expect("Failed to create case-insensitive regex set")
});

#[inline]
pub fn get_patterns(
    ignore_case: bool,
) -> (
    &'static HashMap<&'static str, Vec<Regex>>,
    &'static RegexSet,
) {
    if ignore_case {
        (
            &*PATTERNS_COMPILED_CASE_INSENSITIVE,
            &*PATTERNS_SET_CASE_INSENSITIVE,
        )
    } else {
        (
            &*PATTERNS_COMPILED_CASE_SENSITIVE,
            &*PATTERNS_SET_CASE_SENSITIVE,
        )
    }
}
