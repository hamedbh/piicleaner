//! PII Cleaner - A Polars extension for removing personally identifiable information

mod patterns;
use pyo3::prelude::*;

/// Detect PII in a string and return match information
#[pyfunction]
fn detect_pii(text: &str) -> PyResult<Vec<(usize, usize, String)>> {
    // For now, let's just detect a simple email pattern
    let email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b";
    let re = regex::Regex::new(email_pattern).unwrap();

    let matches: Vec<(usize, usize, String)> = re
        .find_iter(text)
        .map(|m| (m.start(), m.end(), m.as_str().to_string()))
        .collect();

    Ok(matches)
}

/// Clean PII from a string using the specified method
#[pyfunction]
fn clean_pii(text: &str, cleaning: &str) -> PyResult<String> {
    let email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b";
    let re = regex::Regex::new(email_pattern).unwrap();

    if !re.is_match(text) {
        // No PII found, return original text
        return Ok(text.to_string());
    }

    match cleaning {
        "replace" => Ok("[PII detected, comment redacted.]".to_string()),
        "redact" => {
            let result = re.replace_all(text, |caps: &regex::Captures| {
                "-".repeat(caps.get(0).unwrap().as_str().len())
            });
            Ok(result.to_string())
        }
        _ => Err(pyo3::exceptions::PyValueError::new_err(
            "Unrecognised value for `cleaning`. Use 'replace' or 'redact'.",
        )),
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn _internal(_py: Python, _m: &Bound<'_, PyModule>) -> PyResult<()> {
    _m.add_function(wrap_pyfunction!(detect_pii, _m)?)?;
    _m.add_function(wrap_pyfunction!(clean_pii, _m)?)?;
    Ok(())
}
