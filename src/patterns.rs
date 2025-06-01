//! PII regex patterns

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
    REGISTRY.get_or_init(|| PatternRegistry::new())
}

pub fn get_all_patterns() -> Vec<&'static str> {
    get_registry().get_all_patterns()
}

pub fn get_patterns_by_name(cleaners: &[&str]) -> Vec<&'static str> {
    get_registry().get_patterns_by_name(cleaners)
}
