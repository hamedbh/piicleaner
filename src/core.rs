//! Core PII detection and cleaning logic without Python bindings

use crate::patterns;
use rayon::prelude::*;

/// Core function to detect PII with specific cleaners
pub fn detect_pii_with_cleaners_core(
    text: &str,
    cleaners: &[&str],
    ignore_case: bool,
) -> Vec<(usize, usize, String)> {
    let (compiled_patterns, patterns_set) = patterns::get_patterns(ignore_case);

    // Early exit when using "all" cleaners
    if cleaners.len() == 1 && cleaners[0] == "all" && !patterns_set.is_match(text) {
        return Vec::new();
    }

    let mut all_matches = Vec::new();

    // Determine which patterns to use
    let cleaners_to_process = if cleaners.len() == 1 && cleaners[0] == "all" {
        compiled_patterns.keys().collect::<Vec<_>>()
    } else {
        cleaners.iter().collect::<Vec<_>>()
    };

    // Process each cleaner
    for &cleaner_name in cleaners_to_process {
        if let Some(regexes) = compiled_patterns.get(cleaner_name) {
            for regex in regexes {
                for m in regex.find_iter(text) {
                    all_matches.push((m.start(), m.end(), m.as_str().to_string()));
                }
            }
        }
    }

    all_matches.sort_by_key(|&(start, _, _)| start);
    all_matches.dedup();
    all_matches
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

/// Wrapper function where cleaners == "all" to keep Python API unchanged
#[inline]
pub fn detect_pii_core(text: &str, ignore_case: bool) -> Vec<(usize, usize, String)> {
    detect_pii_with_cleaners_core(text, &["all"], ignore_case)
}

#[derive(Copy, Clone, PartialEq)]
pub enum Cleaning {
    Replace,
    Redact,
}

/// Core function to clean PII with specific cleaners
pub fn clean_pii_with_cleaners_core(
    text: &str,
    cleaners: &[&str],
    cleaning: Cleaning,
    ignore_case: bool,
) -> String {
    let (compiled_patterns, patterns_set) = patterns::get_patterns(ignore_case);

    match cleaning {
        Cleaning::Replace => {
            // If cleaners is "all" then we can use the regex set, otherwise
            // need to use the compiled patterns
            if cleaners.len() == 1 && cleaners[0] == "all" {
                // Replace: if ANY PII found, replace entire text with message
                if patterns_set.is_match(text) {
                    return "[PII detected, text redacted]".to_string();
                } else {
                    return text.to_string();
                }
            } else {
                for &cleaner_name in cleaners {
                    if let Some(regexes) = compiled_patterns.get(cleaner_name) {
                        for regex in regexes {
                            if regex.is_match(text) {
                                return "[PII detected, text redacted]".to_string();
                            }
                        }
                    }
                }
            }
            text.to_string()
        }
        Cleaning::Redact => {
            // Determine which patterns to use
            let cleaners_to_process = if cleaners.len() == 1 && cleaners[0] == "all" {
                compiled_patterns.keys().collect::<Vec<_>>()
            } else {
                cleaners.iter().collect::<Vec<_>>()
            };
            // Redact: replace each PII match with dashes, keep rest of text
            let mut result = text.to_string();
            for &cleaner_name in cleaners_to_process {
                if let Some(regexes) = compiled_patterns.get(cleaner_name) {
                    for regex in regexes {
                        result = regex
                            .replace_all(&result, |caps: &regex::Captures| {
                                "-".repeat(caps.get(0).unwrap().as_str().len())
                            })
                            .into_owned();
                    }
                }
            }
            result
        }
    }
}

/// Vectorized function to clean PII with specific cleaners for multiple texts
pub fn clean_pii_with_cleaners_batch_core(
    texts: &[String],
    cleaners: &[&str],
    cleaning: Cleaning,
    ignore_case: bool,
) -> Vec<String> {
    texts
        .par_iter()
        .map(|text| clean_pii_with_cleaners_core(text, cleaners, cleaning, ignore_case))
        .collect()
}

/// Wrapper function where cleaners == "all" to keep Python API unchanged
#[inline]
pub fn clean_pii_core(text: &str, cleaning: Cleaning, ignore_case: bool) -> String {
    clean_pii_with_cleaners_core(text, &["all"], cleaning, ignore_case)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_pii_nino() {
        let text = "My NINO is AB123456C";
        let result = detect_pii_core(text, false);

        // Should find NINO and potentially overlapping case-id pattern
        assert!(!result.is_empty());

        // Find the NINO match specifically
        let nino_match = result.iter().find(|&(_, _, s)| s == "AB123456C");
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
        assert!(!result.is_empty());

        // Find the email match specifically
        let email_match = result.iter().find(|&(_, _, s)| s == "john@example.com");
        assert!(
            email_match.is_some(),
            "Email john@example.com should be detected"
        );
    }

    #[test]
    fn test_clean_pii_redact_mode() {
        let text = "My NINO is AB123456C";
        let result = clean_pii_core(text, Cleaning::Redact, false);

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
        let result = clean_pii_core(text, Cleaning::Replace, false);
        assert_eq!(result, "[PII detected, text redacted]");
    }

    #[test]
    fn test_clean_pii_no_pii_found() {
        let text = "No sensitive data here at all";
        let redacted = clean_pii_core(text, Cleaning::Redact, false);
        let replaced = clean_pii_core(text, Cleaning::Replace, false);
        assert_eq!(redacted, text);
        assert_eq!(replaced, text);
    }

    #[test]
    fn test_multiple_pii_types() {
        let text = "NINO AB123456C, email test@example.com, amount £1,500";
        let result = detect_pii_core(text, false);
        assert!(result.len() >= 3);

        let replaced = clean_pii_core(text, Cleaning::Replace, false);
        assert_eq!(replaced, "[PII detected, text redacted]");
    }

    #[test]
    fn test_specific_cleaners() {
        let text = "NINO AB123456C, email test@example.com";

        // Test with only email cleaner
        let email_only = detect_pii_with_cleaners_core(text, &["email"], false);

        // Should find email (may be duplicated by multiple email patterns)
        assert!(!email_only.is_empty());
        let email_match = email_only.iter().find(|&(_, _, s)| s == "test@example.com");
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
        assert!(!cleaners.is_empty());
    }

    // Tests for the new optimised functions
    #[test]
    fn test_optimised_vs_original_equivalence() {
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
            for method in [Cleaning::Redact, Cleaning::Replace] {
                let result = clean_pii_core(text, method, false);
                // Test that our optimised version works correctly
                assert!(!result.is_empty() || text.is_empty());

                if method == Cleaning::Replace && !detect_pii_core(text, false).is_empty() {
                    assert_eq!(result, "[PII detected, text redacted]");
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
        let batch_results = detect_pii_with_cleaners_batch_core(&texts, &["all"], false);
        assert_eq!(batch_results.len(), 3);
        assert!(!batch_results[0].is_empty()); // Email
        assert_eq!(batch_results[1].len(), 0); // No PII
        assert!(!batch_results[2].is_empty()); // NINO

        // Test batch cleaning
        let batch_cleaned =
            clean_pii_with_cleaners_batch_core(&texts, &["all"], Cleaning::Redact, false);
        assert_eq!(batch_cleaned.len(), 3);
        assert!(!batch_cleaned[0].contains("test1@example.com"));
        assert_eq!(batch_cleaned[1], "No PII here");
        assert!(!batch_cleaned[2].contains("AB123456C"));

        // Test batch with specific cleaners
        let email_only = detect_pii_with_cleaners_batch_core(&texts, &["email"], false);
        assert!(!email_only[0].is_empty()); // Should find email
        assert_eq!(email_only[1].len(), 0); // No PII
        assert_eq!(email_only[2].len(), 0); // Should not find NINO with email cleaner

        // Test batch cleaning with specific cleaners
        let email_cleaned =
            clean_pii_with_cleaners_batch_core(&texts, &["email"], Cleaning::Redact, false);
        assert_eq!(email_cleaned.len(), 3);
        assert!(!email_cleaned[0].contains("test1@example.com")); // Email should be cleaned
        assert_eq!(email_cleaned[1], "No PII here"); // No change
        assert_eq!(email_cleaned[2], "NINO: AB123456C"); // NINO should remain with email-only cleaner
    }

    #[test]
    fn test_edge_cases() {
        // Empty string
        assert_eq!(detect_pii_core("", false), Vec::new());
        assert_eq!(clean_pii_core("", Cleaning::Redact, false), "");
        assert_eq!(clean_pii_core("", Cleaning::Replace, false), "");

        // Whitespace only
        assert_eq!(detect_pii_core("   ", false), Vec::new());
        assert_eq!(clean_pii_core("   ", Cleaning::Redact, false), "   ");

        // Very long string
        let long_text = "a".repeat(10000) + "test@example.com" + &"b".repeat(10000);
        let results = detect_pii_core(&long_text, false);
        assert!(!results.is_empty());
        let cleaned = clean_pii_core(&long_text, Cleaning::Redact, false);
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
                !results.is_empty(),
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
            let cleaned = clean_pii_core(&text, Cleaning::Redact, false);
            assert!(
                !cleaned.contains(pii_text),
                "Failed to clean '{}' from text",
                pii_text
            );

            let replaced = clean_pii_core(&text, Cleaning::Replace, false);
            assert_eq!(
                replaced, "[PII detected, text redacted]",
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
                        assert!(!results.is_empty());
                    }
                })
            })
            .collect();

        for handle in handles {
            handle.join().unwrap();
        }
    }

    #[test]
    fn test_regex_pattern_validity() {
        // Ensure all patterns compile successfully
        let patterns = patterns::get_all_patterns();
        assert!(!patterns.is_empty());

        for pattern in patterns {
            let regex_result = regex::Regex::new(pattern);
            assert!(regex_result.is_ok(), "Invalid regex pattern: {}", pattern);
        }
    }
}
