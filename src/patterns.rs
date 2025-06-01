//! PII regex patterns

pub fn get_all_patterns() -> Vec<&'static str> {
    vec![
        // Email
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        // UK Postcode
        r"\b[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}\b",
        // Phone number (simplified)
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    ]
}

pub fn get_patterns_by_name(cleaners: &[&str]) -> Vec<&'static str> {
    let mut patterns = Vec::new();

    for cleaner in cleaners {
        match *cleaner {
            "email" => patterns.push(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "postcode" => patterns.push(r"\b[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}\b"),
            "telephone" => patterns.push(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
            _ => {} // Ignore unknown cleaners for now
        }
    }

    patterns
}
