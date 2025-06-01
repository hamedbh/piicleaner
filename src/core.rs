//! Core PII detection and cleaning logic without Python bindings

use crate::patterns;

/// Core function to detect PII patterns in text
pub fn detect_pii_core(text: &str) -> Vec<(usize, usize, String)> {
    let patterns = patterns::get_all_patterns();
    let mut all_matches = Vec::new();

    for pattern in patterns {
        let re = regex::Regex::new(pattern).unwrap();
        let matches: Vec<(usize, usize, String)> = re
            .find_iter(text)
            .map(|m| (m.start(), m.end(), m.as_str().to_string()))
            .collect();
        all_matches.extend(matches);
    }

    all_matches.sort_by_key(|&(start, _, _)| start);
    all_matches
}

/// Core function to clean PII from text
pub fn clean_pii_core(text: &str, cleaning: &str) -> String {
    let patterns = patterns::get_all_patterns();

    match cleaning {
        "replace" => {
            // Replace: if ANY PII found, replace entire text with message
            for pattern in patterns {
                let re = regex::Regex::new(pattern).unwrap();
                if re.is_match(text) {
                    return "[PII detected, comment redacted]".to_string();
                }
            }
            // No PII found, return original text
            text.to_string()
        }
        "redact" => {
            // Redact: replace each PII match with dashes, keep rest of text
            let mut result = text.to_string();
            for pattern in patterns {
                let re = regex::Regex::new(pattern).unwrap();
                result = re
                    .replace_all(&result, |caps: &regex::Captures| {
                        "-".repeat(caps.get(0).unwrap().as_str().len())
                    })
                    .to_string();
            }
            result
        }
        _ => {
            // Default to redact
            let mut result = text.to_string();
            for pattern in patterns {
                let re = regex::Regex::new(pattern).unwrap();
                result = re
                    .replace_all(&result, |caps: &regex::Captures| {
                        "-".repeat(caps.get(0).unwrap().as_str().len())
                    })
                    .to_string();
            }
            result
        }
    }
}

/// Core function to detect PII with specific cleaners
pub fn detect_pii_with_cleaners_core(text: &str, cleaners: &[&str]) -> Vec<(usize, usize, String)> {
    let patterns = if cleaners.len() == 1 && cleaners[0] == "all" {
        patterns::get_all_patterns()
    } else {
        patterns::get_patterns_by_name(cleaners)
    };

    let mut all_matches = Vec::new();

    for pattern in patterns {
        let re = regex::Regex::new(pattern).unwrap();
        let matches: Vec<(usize, usize, String)> = re
            .find_iter(text)
            .map(|m| (m.start(), m.end(), m.as_str().to_string()))
            .collect();
        all_matches.extend(matches);
    }

    all_matches.sort_by_key(|&(start, _, _)| start);
    all_matches
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_pii_nino() {
        let text = "My NINO is AB123456C";
        let result = detect_pii_core(text);

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
        let result = detect_pii_core(text);

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
        let result = clean_pii_core(text, "redact");

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
        let result = clean_pii_core(text, "replace");
        assert_eq!(result, "[PII detected, comment redacted]");
    }

    #[test]
    fn test_clean_pii_no_pii_found() {
        let text = "No sensitive data here at all";
        let redacted = clean_pii_core(text, "redact");
        let replaced = clean_pii_core(text, "replace");
        assert_eq!(redacted, text);
        assert_eq!(replaced, text);
    }

    #[test]
    fn test_multiple_pii_types() {
        let text = "NINO AB123456C, email test@example.com, amount £1,500";
        let result = detect_pii_core(text);
        assert!(result.len() >= 3);

        let replaced = clean_pii_core(text, "replace");
        assert_eq!(replaced, "[PII detected, comment redacted]");
    }

    #[test]
    fn test_specific_cleaners() {
        let text = "NINO AB123456C, email test@example.com";

        // Test with only email cleaner
        let email_only = detect_pii_with_cleaners_core(text, &["email"]);

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
        let nino_only = detect_pii_with_cleaners_core(text, &["nino"]);
        assert_eq!(nino_only.len(), 1);
        assert_eq!(nino_only[0].2, "AB123456C");
    }

    #[test]
    fn test_get_available_cleaners() {
        let registry = patterns::get_registry();
        let cleaners = registry.get_available_cleaners();
        assert!(cleaners.len() > 0);
    }
}
