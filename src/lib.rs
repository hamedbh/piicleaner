use pyo3::prelude::*;

pub mod core;
pub mod patterns;
use core::Cleaning;

// Type aliases to simplify complex return types
type DetectionMatch = (usize, usize, String, String);
type DetectionResult = PyResult<Vec<DetectionMatch>>;
type BatchDetectionResult = PyResult<Vec<Vec<DetectionMatch>>>;

impl Cleaning {
    fn from_str(s: &str) -> PyResult<Self> {
        match s {
            "replace" => Ok(Cleaning::Replace),
            "redact" => Ok(Cleaning::Redact),
            _ => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Invalid cleaning method: {}",
                s
            ))),
        }
    }
}

// ============================================================================
// Detection functions
// ============================================================================

/// Detect PII in a string and return match information
#[pyfunction]
#[pyo3(signature = (text, ignore_case = true))]
pub fn detect_pii(text: &str, ignore_case: bool) -> DetectionResult {
    Ok(core::detect_pii_core(text, ignore_case))
}

/// Detect PII with specific cleaners
#[pyfunction]
#[pyo3(signature = (text, cleaners, ignore_case = true))]
pub fn detect_pii_with_cleaners(
    text: &str,
    cleaners: Vec<String>,
    ignore_case: bool,
) -> DetectionResult {
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    Ok(core::detect_pii_with_cleaners_core(
        text,
        &cleaner_refs,
        ignore_case,
    ))
}

/// Vectorised detect PII for multiple texts
#[pyfunction]
#[pyo3(signature = (texts, ignore_case = true))]
pub fn detect_pii_batch(texts: Vec<String>, ignore_case: bool) -> BatchDetectionResult {
    Ok(core::detect_pii_with_cleaners_batch_core(
        &texts,
        &["all"],
        ignore_case,
    ))
}

/// Vectorised detect PII with specific cleaners for multiple texts
#[pyfunction]
#[pyo3(signature = (texts, cleaners, ignore_case = true))]
pub fn detect_pii_with_cleaners_batch(
    texts: Vec<String>,
    cleaners: Vec<String>,
    ignore_case: bool,
) -> BatchDetectionResult {
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    Ok(core::detect_pii_with_cleaners_batch_core(
        &texts,
        &cleaner_refs,
        ignore_case,
    ))
}

// ============================================================================
// Cleaning functions
// ============================================================================

/// Clean PII from a string using the specified method
#[pyfunction]
#[pyo3(signature = (text, cleaning, ignore_case = true, replace_string = None))]
pub fn clean_pii(
    text: &str,
    cleaning: &str,
    ignore_case: bool,
    replace_string: Option<String>,
) -> PyResult<String> {
    let cleaning_enum = Cleaning::from_str(cleaning)?;
    let replace_str = replace_string.as_deref();
    Ok(core::clean_pii_core(
        text,
        cleaning_enum,
        ignore_case,
        replace_str,
    ))
}

/// Clean PII with specific cleaners
#[pyfunction]
#[pyo3(signature = (text, cleaners, cleaning, ignore_case = true, replace_string = None))]
pub fn clean_pii_with_cleaners(
    text: &str,
    cleaners: Vec<String>,
    cleaning: &str,
    ignore_case: bool,
    replace_string: Option<String>,
) -> PyResult<String> {
    let cleaning_enum = Cleaning::from_str(cleaning)?;
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    let replace_str = replace_string.as_deref();
    Ok(core::clean_pii_with_cleaners_core(
        text,
        &cleaner_refs,
        cleaning_enum,
        ignore_case,
        replace_str,
    ))
}

/// Vectorised clean PII for multiple texts
#[pyfunction]
#[pyo3(signature = (texts, cleaning, ignore_case = true, replace_string = None))]
pub fn clean_pii_batch(
    texts: Vec<String>,
    cleaning: &str,
    ignore_case: bool,
    replace_string: Option<String>,
) -> PyResult<Vec<String>> {
    let cleaning_enum = Cleaning::from_str(cleaning)?;
    let replace_str = replace_string.as_deref();
    Ok(core::clean_pii_with_cleaners_batch_core(
        &texts,
        &["all"],
        cleaning_enum,
        ignore_case,
        replace_str,
    ))
}

/// Vectorised clean PII with specific cleaners for multiple texts
#[pyfunction]
#[pyo3(signature = (texts, cleaners, cleaning, ignore_case = true, replace_string = None))]
pub fn clean_pii_with_cleaners_batch(
    texts: Vec<String>,
    cleaners: Vec<String>,
    cleaning: &str,
    ignore_case: bool,
    replace_string: Option<String>,
) -> PyResult<Vec<String>> {
    let cleaning_enum = Cleaning::from_str(cleaning)?;
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    let replace_str = replace_string.as_deref();
    Ok(core::clean_pii_with_cleaners_batch_core(
        &texts,
        &cleaner_refs,
        cleaning_enum,
        ignore_case,
        replace_str,
    ))
}

// ============================================================================
// Utility functions
// ============================================================================

/// Get list of available cleaner names
#[pyfunction]
pub fn get_available_cleaners() -> PyResult<Vec<String>> {
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
    // Detection functions
    m.add_function(wrap_pyfunction!(detect_pii, m)?)?;
    m.add_function(wrap_pyfunction!(detect_pii_with_cleaners, m)?)?;
    m.add_function(wrap_pyfunction!(detect_pii_batch, m)?)?;
    m.add_function(wrap_pyfunction!(detect_pii_with_cleaners_batch, m)?)?;

    // Cleaning functions
    m.add_function(wrap_pyfunction!(clean_pii, m)?)?;
    m.add_function(wrap_pyfunction!(clean_pii_with_cleaners, m)?)?;
    m.add_function(wrap_pyfunction!(clean_pii_batch, m)?)?;
    m.add_function(wrap_pyfunction!(clean_pii_with_cleaners_batch, m)?)?;

    // Utility functions
    m.add_function(wrap_pyfunction!(get_available_cleaners, m)?)?;

    Ok(())
}
