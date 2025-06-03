use pyo3::prelude::*;

mod core;
pub mod patterns;

/// Detect PII in a string and return match information
#[pyfunction]
#[pyo3(signature = (text, ignore_case = true))]
pub fn detect_pii(text: &str, ignore_case: bool) -> PyResult<Vec<(usize, usize, String)>> {
    Ok(core::detect_pii_core(text, ignore_case))
}

/// Clean PII from a string using the specified method
#[pyfunction]
#[pyo3(signature = (text, cleaning, ignore_case = true))]
pub fn clean_pii(text: &str, cleaning: &str, ignore_case: bool) -> PyResult<String> {
    Ok(core::clean_pii_core(text, cleaning, ignore_case))
}

/// Detect PII with specific cleaners
#[pyfunction]
#[pyo3(signature = (text, cleaners, ignore_case = true))]
pub fn detect_pii_with_cleaners(
    text: &str,
    cleaners: Vec<String>,
    ignore_case: bool,
) -> PyResult<Vec<(usize, usize, String)>> {
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    Ok(core::detect_pii_with_cleaners_core(text, &cleaner_refs, ignore_case))
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
#[pyo3(signature = (texts, ignore_case = true))]
pub fn detect_pii_batch(texts: Vec<String>, ignore_case: bool) -> PyResult<Vec<Vec<(usize, usize, String)>>> {
    Ok(core::detect_pii_batch_core(&texts, ignore_case))
}

/// Vectorized clean PII for multiple texts
#[pyfunction]
#[pyo3(signature = (texts, cleaning, ignore_case = true))]
pub fn clean_pii_batch(texts: Vec<String>, cleaning: &str, ignore_case: bool) -> PyResult<Vec<String>> {
    Ok(core::clean_pii_batch_core(&texts, cleaning, ignore_case))
}

/// Vectorized detect PII with specific cleaners for multiple texts
#[pyfunction]
#[pyo3(signature = (texts, cleaners, ignore_case = true))]
pub fn detect_pii_with_cleaners_batch(
    texts: Vec<String>,
    cleaners: Vec<String>,
    ignore_case: bool,
) -> PyResult<Vec<Vec<(usize, usize, String)>>> {
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    Ok(core::detect_pii_with_cleaners_batch_core(
        &texts,
        &cleaner_refs,
        ignore_case,
    ))
}

/// Vectorized clean PII with specific cleaners for multiple texts
#[pyfunction]
#[pyo3(signature = (texts, cleaners, cleaning, ignore_case = true))]
pub fn clean_pii_with_cleaners_batch(
    texts: Vec<String>,
    cleaners: Vec<String>,
    cleaning: &str,
    ignore_case: bool,
) -> PyResult<Vec<String>> {
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    Ok(core::clean_pii_with_cleaners_batch_core(
        &texts,
        &cleaner_refs,
        cleaning,
        ignore_case,
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
