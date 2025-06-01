use pyo3::prelude::*;

mod patterns;

/// Detect PII in a string and return match information
#[pyfunction]
fn detect_pii(text: &str) -> PyResult<Vec<(usize, usize, String)>> {
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
    Ok(all_matches)
}

/// Clean PII from a string using the specified method
#[pyfunction]
fn clean_pii(text: &str, cleaning: &str) -> PyResult<String> {
    let patterns = patterns::get_all_patterns();
    
    match cleaning {
        "replace" => {
            // Replace: if ANY PII found, replace entire text with message
            for pattern in patterns {
                let re = regex::Regex::new(pattern).unwrap();
                if re.is_match(text) {
                    return Ok("[PII detected, comment redacted]".to_string());
                }
            }
            // No PII found, return original text
            Ok(text.to_string())
        },
        "redact" => {
            // Redact: replace each PII match with dashes, keep rest of text
            let mut result = text.to_string();
            for pattern in patterns {
                let re = regex::Regex::new(pattern).unwrap();
                result = re.replace_all(&result, |caps: &regex::Captures| {
                    "-".repeat(caps.get(0).unwrap().as_str().len())
                }).to_string();
            }
            Ok(result)
        },
        _ => {
            // Default to redact
            let mut result = text.to_string();
            for pattern in patterns {
                let re = regex::Regex::new(pattern).unwrap();
                result = re.replace_all(&result, |caps: &regex::Captures| {
                    "-".repeat(caps.get(0).unwrap().as_str().len())
                }).to_string();
            }
            Ok(result)
        }
    }
}

/// Detect PII with specific cleaners
#[pyfunction]
fn detect_pii_with_cleaners(
    text: &str,
    cleaners: Vec<String>,
) -> PyResult<Vec<(usize, usize, String)>> {
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    let patterns = if cleaners.len() == 1 && cleaners[0] == "all" {
        patterns::get_all_patterns()
    } else {
        patterns::get_patterns_by_name(&cleaner_refs)
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
    Ok(all_matches)
}

/// Get list of available cleaner names
#[pyfunction]
fn get_available_cleaners() -> PyResult<Vec<String>> {
    let registry = patterns::get_registry();
    let cleaners: Vec<String> = registry
        .get_available_cleaners()
        .iter()
        .map(|&s| s.to_string())
        .collect();
    Ok(cleaners)
}

#[pymodule]
fn _internal(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(detect_pii, m)?)?;
    m.add_function(wrap_pyfunction!(clean_pii, m)?)?;
    m.add_function(wrap_pyfunction!(detect_pii_with_cleaners, m)?)?;
    m.add_function(wrap_pyfunction!(get_available_cleaners, m)?)?;
    Ok(())
}
