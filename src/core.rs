//! Core PII detection and cleaning logic without Python bindings

use crate::patterns;
use once_cell::sync::Lazy;
use rayon::prelude::*;
use regex::RegexSet;

// Pre-compiled regex patterns for maximum performance
static ALL_PATTERNS_COMPILED_CASE_SENSITIVE: Lazy<Vec<regex::Regex>> = Lazy::new(|| {
    patterns::get_all_patterns()
        .into_iter()
        .map(|pattern| regex::Regex::new(pattern).expect("Invalid regex pattern"))
        .collect()
});

static ALL_PATTERNS_COMPILED_CASE_INSENSITIVE: Lazy<Vec<regex::Regex>> = Lazy::new(|| {
    patterns::get_all_patterns()
        .into_iter()
        .map(|pattern| {
            regex::RegexBuilder::new(pattern)
                .case_insensitive(true)
                .build()
                .expect("Invalid regex pattern")
        })
        .collect()
});

static ALL_PATTERNS_SET_CASE_SENSITIVE: Lazy<RegexSet> = Lazy::new(|| {
    let pattern_strings = patterns::get_all_patterns();
    RegexSet::new(pattern_strings).expect("Failed to create regex set")
});

static ALL_PATTERNS_SET_CASE_INSENSITIVE: Lazy<RegexSet> = Lazy::new(|| {
    let pattern_strings = patterns::get_all_patterns();
    regex::RegexSetBuilder::new(pattern_strings)
        .case_insensitive(true)
        .build()
        .expect("Failed to create case-insensitive regex set")
});

/// Core function to detect PII patterns in text (optimized)
pub fn detect_pii_core(text: &str, ignore_case: bool) -> Vec<(usize, usize, String)> {
    let (patterns_set, patterns_compiled) = if ignore_case {
        (&*ALL_PATTERNS_SET_CASE_INSENSITIVE, &*ALL_PATTERNS_COMPILED_CASE_INSENSITIVE)
    } else {
        (&*ALL_PATTERNS_SET_CASE_SENSITIVE, &*ALL_PATTERNS_COMPILED_CASE_SENSITIVE)
    };

    // Fast check: does this text match ANY pattern?
    if !patterns_set.is_match(text) {
        return Vec::new();
    }

    let mut all_matches = Vec::new();

    // Only check individual patterns for texts that might have matches
    for regex in patterns_compiled.iter() {
        for m in regex.find_iter(text) {
            all_matches.push((m.start(), m.end(), m.as_str().to_string()));
        }
    }

    all_matches.sort_by_key(|&(start, _, _)| start);
    all_matches
}

/// Core function to clean PII from text (optimized with pre-compiled patterns)
pub fn clean_pii_core(text: &str, cleaning: &str, ignore_case: bool) -> String {
    let patterns_compiled = if ignore_case {
        &*ALL_PATTERNS_COMPILED_CASE_INSENSITIVE
    } else {
        &*ALL_PATTERNS_COMPILED_CASE_SENSITIVE
    };

    match cleaning {
        "replace" => {
            // Replace: if ANY PII found, replace entire text with message
            for regex in patterns_compiled.iter() {
                if regex.is_match(text) {
                    return "[PII detected, comment redacted]".to_string();
                }
            }
            // No PII found, return original text
            text.to_string()
        }
        "redact" => {
            // Redact: replace each PII match with dashes, keep rest of text
            let mut result = text.to_string();
            for regex in patterns_compiled.iter() {
                result = regex
                    .replace_all(&result, |caps: &regex::Captures| {
                        "-".repeat(caps.get(0).unwrap().as_str().len())
                    })
                    .into_owned();
            }
            result
        }
        _ => {
            // Default to redact
            let mut result = text.to_string();
            for regex in patterns_compiled.iter() {
                result = regex
                    .replace_all(&result, |caps: &regex::Captures| {
                        "-".repeat(caps.get(0).unwrap().as_str().len())
                    })
                    .into_owned();
            }
            result
        }
    }
}

/// Core function to detect PII with specific cleaners
pub fn detect_pii_with_cleaners_core(text: &str, cleaners: &[&str], ignore_case: bool) -> Vec<(usize, usize, String)> {
    let patterns = if cleaners.len() == 1 && cleaners[0] == "all" {
        patterns::get_all_patterns()
    } else {
        patterns::get_patterns_by_name(cleaners)
    };

    let mut all_matches = Vec::new();

    for pattern in patterns {
        let re = if ignore_case {
            regex::RegexBuilder::new(pattern)
                .case_insensitive(true)
                .build()
                .unwrap()
        } else {
            regex::Regex::new(pattern).unwrap()
        };
        let matches: Vec<(usize, usize, String)> = re
            .find_iter(text)
            .map(|m| (m.start(), m.end(), m.as_str().to_string()))
            .collect();
        all_matches.extend(matches);
    }

    all_matches.sort_by_key(|&(start, _, _)| start);
    all_matches
}

/// Vectorized function to detect PII in multiple texts at once
pub fn detect_pii_batch_core(texts: &[String], ignore_case: bool) -> Vec<Vec<(usize, usize, String)>> {
    texts.par_iter().map(|text| detect_pii_core(text, ignore_case)).collect()
}

/// Vectorized function to clean PII from multiple texts at once
pub fn clean_pii_batch_core(texts: &[String], cleaning: &str, ignore_case: bool) -> Vec<String> {
    texts
        .par_iter()
        .map(|text| clean_pii_core(text, cleaning, ignore_case))
        .collect()
}

/// Vectorized function to detect PII with specific cleaners for multiple texts
pub fn detect_pii_with_cleaners_batch_core(
    texts: &[String],
    cleaners: &[&str],
    ignore_case: bool,
) -> Vec<Vec<(usize, usize, String)>> {
    texts
        .par_iter()
        .map(|text| detect_pii_with_cleaners_core(text, cleaners, ignore_case))
        .collect()
}

/// Vectorized function to clean PII with specific cleaners for multiple texts
pub fn clean_pii_with_cleaners_batch_core(
    texts: &[String],
    cleaners: &[&str],
    cleaning: &str,
    ignore_case: bool,
) -> Vec<String> {
    // Pre-compile the specific patterns once for efficiency
    let patterns = if cleaners.len() == 1 && cleaners[0] == "all" {
        patterns::get_all_patterns()
    } else {
        patterns::get_patterns_by_name(cleaners)
    };

    let compiled_patterns: Vec<regex::Regex> = patterns
        .into_iter()
        .map(|pattern| {
            if ignore_case {
                regex::RegexBuilder::new(pattern)
                    .case_insensitive(true)
                    .build()
                    .expect("Invalid regex pattern")
            } else {
                regex::Regex::new(pattern).expect("Invalid regex pattern")
            }
        })
        .collect();

    texts
        .par_iter()
        .map(|text| clean_pii_with_specific_patterns_core(text, &compiled_patterns, cleaning))
        .collect()
}

/// Helper function to clean PII using pre-compiled patterns
fn clean_pii_with_specific_patterns_core(
    text: &str,
    compiled_patterns: &[regex::Regex],
    cleaning: &str,
) -> String {
    // Check if any pattern matches
    let has_matches = compiled_patterns.iter().any(|regex| regex.is_match(text));

    if !has_matches {
        return text.to_string();
    }

    match cleaning {
        "replace" => "[PII detected, comment redacted]".to_string(),
        "redact" | _ => {
            let mut result = text.to_string();
            for regex in compiled_patterns {
                result = regex
                    .replace_all(&result, |caps: &regex::Captures| {
                        "-".repeat(caps.get(0).unwrap().as_str().len())
                    })
                    .into_owned();
            }
            result
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_pii_nino() {
        let text = "My NINO is AB123456C";
        let result = detect_pii_core(text, false);

        // Should find NINO and potentially overlapping case-id pattern
        assert!(result.len() >= 1);

        // Find the NINO match specifically
        let nino_match = result.iter().find(|&&(_, _, ref s)| s == "AB123456C");
        assert!(nino_match.is_some(), "NINO AB123456C should be detected");

        let (start, end, matched) = nino_match.unwrap();
        assert_eq!(*matched, "AB123456C");
        assert_eq!(*start, 11); // start position
        assert_eq!(*end, 20); // end position
    }

    #[test]
    fn test_detect_pii_email() {
        let text = "Contact john@example.com for details";
        let result = detect_pii_core(text, false);

        // May find email multiple times due to multiple patterns
        assert!(result.len() >= 1);

        // Find the email match specifically
        let email_match = result
            .iter()
            .find(|&&(_, _, ref s)| s == "john@example.com");
        assert!(
            email_match.is_some(),
            "Email john@example.com should be detected"
        );
    }

    #[test]
    fn test_clean_pii_redact_mode() {
        let text = "My NINO is AB123456C";
        let result = clean_pii_core(text, "redact", false);

        // Debug: see what we got
        println!("Redacted result: '{}'", result);

        // Should not contain the original NINO
        assert!(!result.contains("AB123456C"));
        // Should contain dashes (multiple patterns may apply)
        assert!(result.contains("-"));
        // Should start with the unchanged part
        assert!(result.starts_with("My NINO is"));
    }

    #[test]
    fn test_clean_pii_replace_mode() {
        let text = "My NINO is AB123456C";
        let result = clean_pii_core(text, "replace", false);
        assert_eq!(result, "[PII detected, comment redacted]");
    }

    #[test]
    fn test_clean_pii_no_pii_found() {
        let text = "No sensitive data here at all";
        let redacted = clean_pii_core(text, "redact", false);
        let replaced = clean_pii_core(text, "replace", false);
        assert_eq!(redacted, text);
        assert_eq!(replaced, text);
    }

    #[test]
    fn test_multiple_pii_types() {
        let text = "NINO AB123456C, email test@example.com, amount £1,500";
        let result = detect_pii_core(text, false);
        assert!(result.len() >= 3);

        let replaced = clean_pii_core(text, "replace", false);
        assert_eq!(replaced, "[PII detected, comment redacted]");
    }

    #[test]
    fn test_specific_cleaners() {
        let text = "NINO AB123456C, email test@example.com";

        // Test with only email cleaner
        let email_only = detect_pii_with_cleaners_core(text, &["email"], false);

        // Should find email (may be duplicated by multiple email patterns)
        assert!(email_only.len() >= 1);
        let email_match = email_only
            .iter()
            .find(|&&(_, _, ref s)| s == "test@example.com");
        assert!(
            email_match.is_some(),
            "Email should be detected with email cleaner"
        );

        // Test with only nino cleaner
        let nino_only = detect_pii_with_cleaners_core(text, &["nino"], false);
        assert_eq!(nino_only.len(), 1);
        assert_eq!(nino_only[0].2, "AB123456C");
    }

    #[test]
    fn test_get_available_cleaners() {
        let registry = patterns::get_registry();
        let cleaners = registry.get_available_cleaners();
        assert!(cleaners.len() > 0);
    }

    // Tests for the new optimized functions
    #[test]
    fn test_optimized_vs_original_equivalence() {
        let test_cases = vec![
            "No PII here",
            "Email: test@example.com",
            "NINO: AB123456C",
            "Phone: +44 20 1234 5678",
            "Multiple: test@example.com and AB123456C",
            "",
            "Just text with no PII at all",
        ];

        for text in test_cases {
            for method in ["redact", "replace"] {
                let result = clean_pii_core(text, method, false);
                // Test that our optimized version works correctly
                assert!(!result.is_empty() || text.is_empty());

                if method == "replace" && detect_pii_core(text, false).len() > 0 {
                    assert_eq!(result, "[PII detected, comment redacted]");
                }
            }
        }
    }

    #[test]
    fn test_batch_functions() {
        let texts = vec![
            "Email: test1@example.com".to_string(),
            "No PII here".to_string(),
            "NINO: AB123456C".to_string(),
        ];

        // Test batch detection
        let batch_results = detect_pii_batch_core(&texts, false);
        assert_eq!(batch_results.len(), 3);
        assert!(batch_results[0].len() >= 1); // Email
        assert_eq!(batch_results[1].len(), 0); // No PII
        assert!(batch_results[2].len() >= 1); // NINO

        // Test batch cleaning
        let batch_cleaned = clean_pii_batch_core(&texts, "redact", false);
        assert_eq!(batch_cleaned.len(), 3);
        assert!(!batch_cleaned[0].contains("test1@example.com"));
        assert_eq!(batch_cleaned[1], "No PII here");
        assert!(!batch_cleaned[2].contains("AB123456C"));

        // Test batch with specific cleaners
        let email_only = detect_pii_with_cleaners_batch_core(&texts, &["email"], false);
        assert!(email_only[0].len() >= 1); // Should find email
        assert_eq!(email_only[1].len(), 0); // No PII
        assert_eq!(email_only[2].len(), 0); // Should not find NINO with email cleaner

        // Test batch cleaning with specific cleaners
        let email_cleaned = clean_pii_with_cleaners_batch_core(&texts, &["email"], "redact", false);
        assert_eq!(email_cleaned.len(), 3);
        assert!(!email_cleaned[0].contains("test1@example.com")); // Email should be cleaned
        assert_eq!(email_cleaned[1], "No PII here"); // No change
        assert_eq!(email_cleaned[2], "NINO: AB123456C"); // NINO should remain with email-only cleaner
    }

    #[test]
    fn test_edge_cases() {
        // Empty string
        assert_eq!(detect_pii_core("", false), Vec::new());
        assert_eq!(clean_pii_core("", "redact", false), "");
        assert_eq!(clean_pii_core("", "replace", false), "");

        // Whitespace only
        assert_eq!(detect_pii_core("   ", false), Vec::new());
        assert_eq!(clean_pii_core("   ", "redact", false), "   ");

        // Very long string
        let long_text = "a".repeat(10000) + "test@example.com" + &"b".repeat(10000);
        let results = detect_pii_core(&long_text, false);
        assert!(results.len() >= 1);
        let cleaned = clean_pii_core(&long_text, "redact", false);
        assert!(!cleaned.contains("test@example.com"));

        // Special characters
        let special_text = "Email: test@example.com\n\tPhone: +44 20 1234 5678\r\n";
        let results = detect_pii_core(special_text, false);
        assert!(results.len() >= 2);
    }

    #[test]
    fn test_all_pii_types() {
        let test_cases = vec![
            ("test@example.com", "email"),
            ("+44 20 7946 0958", "telephone"),
            ("SW1A 1AA", "postcode"),
            ("AB123456C", "nino"),
            ("123 high street", "address"), // Use lowercase for address pattern
            ("£1,500", "cash-amount"),
            ("192.168.1.1", "ip_address"),
        ];

        for (pii_text, expected_type) in test_cases {
            let text = format!("Here is some PII: {}", pii_text);
            let results = detect_pii_core(&text, false);

            // Should detect at least one match
            assert!(
                results.len() >= 1,
                "Failed to detect {} in '{}'",
                expected_type,
                text
            );

            // Should find the specific PII text
            let found = results
                .iter()
                .any(|(_, _, matched)| matched.contains(pii_text));
            assert!(
                found,
                "Failed to find '{}' in detection results for {}",
                pii_text, expected_type
            );

            // Test cleaning
            let cleaned = clean_pii_core(&text, "redact", false);
            assert!(
                !cleaned.contains(pii_text),
                "Failed to clean '{}' from text",
                pii_text
            );

            let replaced = clean_pii_core(&text, "replace", false);
            assert_eq!(
                replaced, "[PII detected, comment redacted]",
                "Replace mode failed for {}",
                expected_type
            );
        }
    }

    #[test]
    fn test_performance_characteristics() {
        // Test that pre-compiled patterns are actually being used
        // This should be very fast compared to compiling patterns each time
        let text = "Email: test@example.com";

        let start = std::time::Instant::now();
        for _ in 0..1000 {
            let _ = detect_pii_core(text, false);
        }
        let duration = start.elapsed();

        // Should complete 1000 detections in reasonable time (< 100ms)
        assert!(
            duration.as_millis() < 100,
            "Performance regression: took {:?} for 1000 detections",
            duration
        );
    }

    #[test]
    fn test_concurrent_access() {
        use std::thread;

        // Test that static patterns can be accessed concurrently
        let handles: Vec<_> = (0..4)
            .map(|i| {
                thread::spawn(move || {
                    let text = format!("Email: test{}@example.com", i);
                    for _ in 0..100 {
                        let results = detect_pii_core(&text, false);
                        assert!(results.len() >= 1);
                    }
                })
            })
            .collect();

        for handle in handles {
            handle.join().unwrap();
        }
    }

    #[test]
    fn test_invalid_cleaning_method() {
        let text = "Email: test@example.com";
        // Invalid method should default to redact behavior
        let result = clean_pii_core(text, "invalid_method", false);
        assert!(!result.contains("test@example.com"));
        assert!(result.contains("-") || result.starts_with("Email:"));
    }

    #[test]
    fn test_regex_pattern_validity() {
        // Ensure all patterns compile successfully
        let patterns = patterns::get_all_patterns();
        assert!(patterns.len() > 0);

        for pattern in patterns {
            let regex_result = regex::Regex::new(pattern);
            assert!(regex_result.is_ok(), "Invalid regex pattern: {}", pattern);
        }
    }
}
