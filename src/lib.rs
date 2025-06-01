use pyo3::prelude::*;

mod core;
pub mod patterns;

/// Detect PII in a string and return match information
#[pyfunction]
pub fn detect_pii(text: &str) -> PyResult<Vec<(usize, usize, String)>> {
    Ok(core::detect_pii_core(text))
}

/// Clean PII from a string using the specified method
#[pyfunction]
pub fn clean_pii(text: &str, cleaning: &str) -> PyResult<String> {
    Ok(core::clean_pii_core(text, cleaning))
}

/// Detect PII with specific cleaners
#[pyfunction]
pub fn detect_pii_with_cleaners(
    text: &str,
    cleaners: Vec<String>,
) -> PyResult<Vec<(usize, usize, String)>> {
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    Ok(core::detect_pii_with_cleaners_core(text, &cleaner_refs))
}

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

/// Vectorized detect PII for multiple texts
#[pyfunction]
pub fn detect_pii_batch(texts: Vec<String>) -> PyResult<Vec<Vec<(usize, usize, String)>>> {
    Ok(core::detect_pii_batch_core(&texts))
}

/// Vectorized clean PII for multiple texts
#[pyfunction]
pub fn clean_pii_batch(texts: Vec<String>, cleaning: &str) -> PyResult<Vec<String>> {
    Ok(core::clean_pii_batch_core(&texts, cleaning))
}

/// Vectorized detect PII with specific cleaners for multiple texts
#[pyfunction]
pub fn detect_pii_with_cleaners_batch(
    texts: Vec<String>,
    cleaners: Vec<String>,
) -> PyResult<Vec<Vec<(usize, usize, String)>>> {
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    Ok(core::detect_pii_with_cleaners_batch_core(
        &texts,
        &cleaner_refs,
    ))
}

/// Vectorized clean PII with specific cleaners for multiple texts
#[pyfunction]
pub fn clean_pii_with_cleaners_batch(
    texts: Vec<String>,
    cleaners: Vec<String>,
    cleaning: &str,
) -> PyResult<Vec<String>> {
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    Ok(core::clean_pii_with_cleaners_batch_core(
        &texts,
        &cleaner_refs,
        cleaning,
    ))
}

#[pymodule]
fn _internal(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(detect_pii, m)?)?;
    m.add_function(wrap_pyfunction!(clean_pii, m)?)?;
    m.add_function(wrap_pyfunction!(detect_pii_with_cleaners, m)?)?;
    m.add_function(wrap_pyfunction!(get_available_cleaners, m)?)?;
    m.add_function(wrap_pyfunction!(detect_pii_batch, m)?)?;
    m.add_function(wrap_pyfunction!(clean_pii_batch, m)?)?;
    m.add_function(wrap_pyfunction!(detect_pii_with_cleaners_batch, m)?)?;
    m.add_function(wrap_pyfunction!(clean_pii_with_cleaners_batch, m)?)?;
    Ok(())
}
