use pyo3::prelude::*;
use rayon::prelude::*;

pub mod core;
pub mod patterns;
mod polars_plugin;
use core::Cleaning;

// Type aliases to simplify complex return types
type DetectionMatch = (usize, usize, String, String);
type DetectionResult = PyResult<Vec<DetectionMatch>>;
type BatchDetectionResult = PyResult<Vec<Vec<DetectionMatch>>>;

impl Cleaning {
    /// Parse a cleaning method name. The error message is shared by the
    /// Python functions and the Polars plugin.
    fn parse(s: &str) -> Result<Self, String> {
        match s {
            "replace" => Ok(Cleaning::Replace),
            "redact" => Ok(Cleaning::Redact),
            _ => Err(format!("Invalid cleaning method: {}", s)),
        }
    }

    fn from_str(s: &str) -> PyResult<Self> {
        Self::parse(s).map_err(PyErr::new::<pyo3::exceptions::PyValueError, _>)
    }
}

/// Check the cleaner list is `["all"]` or a non-empty list of names in the
/// pattern registry, so callers get a clear error instead of a silent no-op
/// or a downstream panic. The error messages are shared by `Cleaner`, the
/// Python functions and the Polars plugin.
fn check_cleaners(cleaners: &[&str]) -> Result<(), String> {
    if cleaners == ["all"] {
        return Ok(());
    }
    let available = patterns::get_registry().get_available_cleaners();
    if cleaners.is_empty() {
        return Err(format!(
            "No cleaners given. Pass \"all\", or one or more of: {:?}",
            available
        ));
    }
    if cleaners.contains(&"all") {
        return Err(format!(
            "\"all\" can't be combined with other cleaners: {:?}. Pass \"all\" on its own, \
             or only specific cleaners",
            cleaners
        ));
    }
    let unknown: Vec<&str> = cleaners
        .iter()
        .filter(|c| !available.contains(c))
        .copied()
        .collect();
    if unknown.is_empty() {
        Ok(())
    } else {
        Err(format!(
            "Unknown cleaner(s): {:?}. Available cleaners: {:?}",
            unknown, available
        ))
    }
}

/// `check_cleaners`, raising a Python `ValueError`
fn validate_cleaners(cleaners: &[&str]) -> PyResult<()> {
    check_cleaners(cleaners).map_err(PyErr::new::<pyo3::exceptions::PyValueError, _>)
}

/// Convert the byte offsets in detection results to character offsets.
///
/// The Rust core reports UTF-8 byte offsets, but Python indexes `str` by code
/// point. A Rust `char` is one code point, so counting chars gives offsets
/// that slice the original Python string correctly.
fn to_char_offsets(text: &str, matches: Vec<DetectionMatch>) -> Vec<DetectionMatch> {
    // Bytes and characters coincide for ASCII text
    if matches.is_empty() || text.is_ascii() {
        return matches;
    }

    // Every byte offset that needs converting, in order
    let mut byte_offsets: Vec<usize> = matches.iter().flat_map(|m| [m.0, m.1]).collect();
    byte_offsets.sort_unstable();
    byte_offsets.dedup();

    // One pass over the text, recording the char count at each byte offset.
    // Match boundaries always fall on char boundaries, and the end of the
    // text is included so a match ending there is converted too.
    let mut char_offsets = Vec::with_capacity(byte_offsets.len());
    let boundaries = text
        .char_indices()
        .map(|(i, _)| i)
        .chain(std::iter::once(text.len()));
    let mut wanted = byte_offsets.iter().peekable();
    for (char_idx, byte_idx) in boundaries.enumerate() {
        while wanted.next_if(|&&b| b == byte_idx).is_some() {
            char_offsets.push(char_idx);
        }
        if wanted.peek().is_none() {
            break;
        }
    }

    let to_char = |byte: usize| {
        let i = byte_offsets
            .binary_search(&byte)
            .expect("match offset is a char boundary");
        char_offsets[i]
    };
    matches
        .into_iter()
        .map(|(start, end, matched, pii_type)| (to_char(start), to_char(end), matched, pii_type))
        .collect()
}

/// Batch version of `to_char_offsets`, converting each text in parallel.
fn to_char_offsets_batch(
    texts: &[String],
    results: Vec<Vec<DetectionMatch>>,
) -> Vec<Vec<DetectionMatch>> {
    texts
        .par_iter()
        .zip(results)
        .map(|(text, matches)| to_char_offsets(text, matches))
        .collect()
}

// ============================================================================
// Detection functions
// ============================================================================

/// Detect PII in a string and return match information. Offsets are
/// character offsets, so they index the Python string directly.
#[pyfunction]
#[pyo3(signature = (text, ignore_case = true))]
pub fn detect_pii(text: &str, ignore_case: bool) -> DetectionResult {
    Ok(to_char_offsets(
        text,
        core::detect_pii_core(text, ignore_case),
    ))
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
    validate_cleaners(&cleaner_refs)?;
    Ok(to_char_offsets(
        text,
        core::detect_pii_with_cleaners_core(text, &cleaner_refs, ignore_case),
    ))
}

/// Vectorised detect PII for multiple texts
#[pyfunction]
#[pyo3(signature = (texts, ignore_case = true))]
pub fn detect_pii_batch(
    py: Python<'_>,
    texts: Vec<String>,
    ignore_case: bool,
) -> BatchDetectionResult {
    Ok(py.detach(|| {
        let results = core::detect_pii_with_cleaners_batch_core(&texts, &["all"], ignore_case);
        to_char_offsets_batch(&texts, results)
    }))
}

/// Vectorised detect PII with specific cleaners for multiple texts
#[pyfunction]
#[pyo3(signature = (texts, cleaners, ignore_case = true))]
pub fn detect_pii_with_cleaners_batch(
    py: Python<'_>,
    texts: Vec<String>,
    cleaners: Vec<String>,
    ignore_case: bool,
) -> BatchDetectionResult {
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    validate_cleaners(&cleaner_refs)?;
    Ok(py.detach(|| {
        let results = core::detect_pii_with_cleaners_batch_core(&texts, &cleaner_refs, ignore_case);
        to_char_offsets_batch(&texts, results)
    }))
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
    validate_cleaners(&cleaner_refs)?;
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
    py: Python<'_>,
    texts: Vec<String>,
    cleaning: &str,
    ignore_case: bool,
    replace_string: Option<String>,
) -> PyResult<Vec<String>> {
    let cleaning_enum = Cleaning::from_str(cleaning)?;
    let replace_str = replace_string.as_deref();
    Ok(py.detach(|| {
        core::clean_pii_with_cleaners_batch_core(
            &texts,
            &["all"],
            cleaning_enum,
            ignore_case,
            replace_str,
        )
    }))
}

/// Vectorised clean PII with specific cleaners for multiple texts
#[pyfunction]
#[pyo3(signature = (texts, cleaners, cleaning, ignore_case = true, replace_string = None))]
pub fn clean_pii_with_cleaners_batch(
    py: Python<'_>,
    texts: Vec<String>,
    cleaners: Vec<String>,
    cleaning: &str,
    ignore_case: bool,
    replace_string: Option<String>,
) -> PyResult<Vec<String>> {
    let cleaning_enum = Cleaning::from_str(cleaning)?;
    let cleaner_refs: Vec<&str> = cleaners.iter().map(|s| s.as_str()).collect();
    validate_cleaners(&cleaner_refs)?;
    let replace_str = replace_string.as_deref();
    Ok(py.detach(|| {
        core::clean_pii_with_cleaners_batch_core(
            &texts,
            &cleaner_refs,
            cleaning_enum,
            ignore_case,
            replace_str,
        )
    }))
}

// ============================================================================
// Utility functions
// ============================================================================

/// Get list of available cleaner names, in priority order
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

#[cfg(test)]
mod tests {
    use super::*;

    fn m(start: usize, end: usize, text: &str) -> DetectionMatch {
        (start, end, text.to_string(), "email".to_string())
    }

    /// Slice by char offsets, the way Python slices a str
    fn char_slice(text: &str, start: usize, end: usize) -> String {
        text.chars().skip(start).take(end - start).collect()
    }

    #[test]
    fn test_ascii_offsets_unchanged() {
        let text = "Contact a@b.com now";
        let matches = vec![m(8, 15, "a@b.com")];
        assert_eq!(to_char_offsets(text, matches.clone()), matches);
    }

    #[test]
    fn test_non_ascii_before_match() {
        // "é" is 2 bytes, "£" is 2 bytes, "😀" is 4 bytes, "東" is 3 bytes
        for prefix in ["Café ", "£100 ", "😀 ", "東京 ", "e\u{301} "] {
            let text = format!("{prefix}a@b.com x");
            let start = text.find("a@b.com").unwrap();
            let result = to_char_offsets(&text, vec![m(start, start + 7, "a@b.com")]);
            let (s, e, _, _) = result[0];
            assert_eq!(char_slice(&text, s, e), "a@b.com", "prefix {prefix:?}");
        }
    }

    #[test]
    fn test_non_ascii_inside_match_and_at_end() {
        let text = "x £1,500";
        let start = text.find('£').unwrap();
        let result = to_char_offsets(text, vec![m(start, text.len(), "£1,500")]);
        assert_eq!((result[0].0, result[0].1), (2, 8));
        assert_eq!(char_slice(text, 2, 8), "£1,500");
    }

    #[test]
    fn test_multiple_and_overlapping_matches() {
        let text = "é a@b.com é c@d.org";
        let a = text.find("a@b.com").unwrap();
        let c = text.find("c@d.org").unwrap();
        let matches = vec![
            m(a, a + 7, "a@b.com"),
            m(a, a + 1, "a"),
            m(c, c + 7, "c@d.org"),
        ];
        let result = to_char_offsets(text, matches);
        let pairs: Vec<(usize, usize)> = result.iter().map(|r| (r.0, r.1)).collect();
        assert_eq!(pairs, vec![(2, 9), (2, 3), (12, 19)]);
    }

    #[test]
    fn test_batch_conversion() {
        let texts = vec!["é a@b.com".to_string(), "a@b.com".to_string()];
        let results = vec![vec![m(3, 10, "a@b.com")], vec![m(0, 7, "a@b.com")]];
        let converted = to_char_offsets_batch(&texts, results);
        assert_eq!((converted[0][0].0, converted[0][0].1), (2, 9));
        assert_eq!((converted[1][0].0, converted[1][0].1), (0, 7));
    }
}
