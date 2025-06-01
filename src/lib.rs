//! PII Cleaner - A Polars extension for removing personally identifiable information

mod patterns;
use pyo3::prelude::*;

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

    // Sort by start position
    all_matches.sort_by_key(|&(start, _, _)| start);
    Ok(all_matches)
}

/// Clean PII from a string using the specified method
#[pyfunction]
fn clean_pii(text: &str, cleaning: &str) -> PyResult<String> {
    let patterns = patterns::get_all_patterns();
    let mut has_pii = false;
    
    // Check if any pattern matches
    for pattern in &patterns {
        let re = regex::Regex::new(pattern).unwrap();
        if re.is_match(text) {
            has_pii = true;
            break;
        }
    }
    
    if !has_pii {
        return Ok(text.to_string());
    }
    
    match cleaning {
        "replace" => Ok("[PII detected, comment redacted.]".to_string()),
        "redact" => {
            let mut result = text.to_string();
            for pattern in patterns {
                let re = regex::Regex::new(pattern).unwrap();
                result = re.replace_all(&result, |caps: &regex::Captures| {
                    "-".repeat(caps.get(0).unwrap().as_str().len())
                }).to_string();
            }
            Ok(result)
        },
        _ => Err(pyo3::exceptions::PyValueError::new_err(
            "Unrecognised value for `cleaning`. Use 'replace' or 'redact'."
        ))
    }
}

/// Detect PII with specific cleaners
#[pyfunction]
fn detect_pii_with_cleaners(text: &str, cleaners: Vec<String>) -> PyResult<Vec<(usize, usize, String)>> {
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
    let cleaners: Vec<String> = registry.get_available_cleaners()
        .iter()
        .map(|&s| s.to_string())
        .collect();
    Ok(cleaners)
}

/// A Python module implemented in Rust.
#[pymodule]
fn _internal(_py: Python, _m: &Bound<'_, PyModule>) -> PyResult<()> {
    _m.add_function(wrap_pyfunction!(detect_pii, _m)?)?;
    _m.add_function(wrap_pyfunction!(clean_pii, _m)?)?;
    _m.add_function(wrap_pyfunction!(detect_pii_with_cleaners, _m)?)?;
    _m.add_function(wrap_pyfunction!(get_available_cleaners, _m)?)?;
    Ok(())
}
