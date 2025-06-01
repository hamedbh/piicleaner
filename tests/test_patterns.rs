use piicleaner::patterns::{get_all_patterns, get_patterns_by_name, get_registry};

#[test]
fn test_pattern_registry_creation() {
    let registry = get_registry();
    let cleaners = registry.get_available_cleaners();

    assert!(!cleaners.is_empty());
    assert!(cleaners.contains(&"email"));
    assert!(cleaners.contains(&"nino"));
    assert!(cleaners.contains(&"postcode"));
    assert!(cleaners.contains(&"telephone"));
    assert!(cleaners.contains(&"cash-amount"));
    assert!(cleaners.contains(&"address"));
    assert!(cleaners.contains(&"case-id"));
    assert!(cleaners.contains(&"tag"));
    assert!(cleaners.contains(&"ip_address"));
}

#[test]
fn test_get_all_patterns() {
    let patterns = get_all_patterns();
    assert!(!patterns.is_empty());

    // Should have multiple patterns (email has 2, case-id has 5, etc.)
    assert!(patterns.len() >= 10);
}

#[test]
fn test_get_patterns_by_name_single() {
    let email_patterns = get_patterns_by_name(&["email"]);
    assert_eq!(email_patterns.len(), 2); // email has 2 patterns

    let nino_patterns = get_patterns_by_name(&["nino"]);
    assert_eq!(nino_patterns.len(), 1); // nino has 1 pattern

    let case_id_patterns = get_patterns_by_name(&["case-id"]);
    assert_eq!(case_id_patterns.len(), 5); // case-id has 5 patterns
}

#[test]
fn test_get_patterns_by_name_multiple() {
    let patterns = get_patterns_by_name(&["email", "nino"]);
    assert_eq!(patterns.len(), 3); // email(2) + nino(1)

    let patterns = get_patterns_by_name(&["postcode", "telephone"]);
    assert_eq!(patterns.len(), 2); // postcode(1) + telephone(1)
}

#[test]
fn test_get_patterns_by_name_nonexistent() {
    let patterns = get_patterns_by_name(&["nonexistent"]);
    assert_eq!(patterns.len(), 0);

    let patterns = get_patterns_by_name(&["email", "nonexistent", "nino"]);
    assert_eq!(patterns.len(), 3); // Only email(2) + nino(1), nonexistent ignored
}

#[test]
fn test_get_patterns_by_name_empty() {
    let patterns = get_patterns_by_name(&[]);
    assert_eq!(patterns.len(), 0);
}

#[test]
fn test_pattern_compilation() {
    let patterns = get_all_patterns();

    // Test that all patterns can be compiled as valid regex
    for pattern in patterns {
        let result = regex::Regex::new(pattern);
        assert!(result.is_ok(), "Pattern should compile: {}", pattern);
    }
}

#[test]
fn test_email_pattern_matching() {
    let email_patterns = get_patterns_by_name(&["email"]);

    let test_cases = vec![
        ("test@example.com", true),
        ("user.name@domain.co.uk", true),
        ("invalid.email", false),
        ("@domain.com", false),
        ("user@", false),
    ];

    for (email, should_match) in test_cases {
        let mut found_match = false;
        for pattern in &email_patterns {
            let re = regex::Regex::new(pattern).unwrap();
            if re.is_match(email) {
                found_match = true;
                break;
            }
        }
        assert_eq!(
            found_match, should_match,
            "Email '{}' match result incorrect",
            email
        );
    }
}

#[test]
fn test_nino_pattern_matching() {
    let nino_patterns = get_patterns_by_name(&["nino"]);
    let re = regex::Regex::new(nino_patterns[0]).unwrap();

    let test_cases = vec![
        ("AB123456C", true),
        ("AB 12 34 56 C", true),
        ("AB  12  34  56  C", true),
        ("QQ123456C", false), // Invalid prefix
        ("AB123456", true),   // Valid without suffix (pattern allows optional suffix)
        ("123456789", false), // Not a NINO
    ];

    for (nino, should_match) in test_cases {
        let matches = re.is_match(nino);
        assert_eq!(
            matches, should_match,
            "NINO '{}' match result incorrect",
            nino
        );
    }
}

#[test]
fn test_postcode_pattern_matching() {
    let postcode_patterns = get_patterns_by_name(&["postcode"]);
    let re = regex::Regex::new(postcode_patterns[0]).unwrap();

    let test_cases = vec![
        ("SW1A 1AA", true),
        ("M1 1AA", true),
        ("B33 8TH", true),
        ("W1A 0AX", true),
        ("INVALID", false),
        ("12345", false),
    ];

    for (postcode, should_match) in test_cases {
        let matches = re.is_match(postcode);
        assert_eq!(
            matches, should_match,
            "Postcode '{}' match result incorrect",
            postcode
        );
    }
}

#[test]
fn test_telephone_pattern_matching() {
    let telephone_patterns = get_patterns_by_name(&["telephone"]);
    let re = regex::Regex::new(telephone_patterns[0]).unwrap();

    let test_cases = vec![
        ("01234 567890", true),
        ("0123 456 7890", true),
        ("+44 123 456 7890", true),
        ("07123456789", true),
        ("123", false), // Too short
        ("abc", false), // Not numeric
    ];

    for (phone, should_match) in test_cases {
        let matches = re.is_match(phone);
        assert_eq!(
            matches, should_match,
            "Phone '{}' match result incorrect",
            phone
        );
    }
}

#[test]
fn test_cash_amount_pattern_matching() {
    let cash_patterns = get_patterns_by_name(&["cash-amount"]);

    let test_cases = vec![
        ("£100", true),
        ("$1,500.50", true),
        ("€999.99", true),
        ("1000 GBP", true),
        ("500 USD", true),
        ("£5", false), // Too short (less than 2 digits)
        ("money", false),
    ];

    for (amount, should_match) in test_cases {
        let mut found_match = false;
        for pattern in &cash_patterns {
            let re = regex::Regex::new(pattern).unwrap();
            if re.is_match(amount) {
                found_match = true;
                break;
            }
        }
        assert_eq!(
            found_match, should_match,
            "Amount '{}' match result incorrect",
            amount
        );
    }
}

#[test]
fn test_ip_address_pattern_matching() {
    let ip_patterns = get_patterns_by_name(&["ip_address"]);
    let re = regex::Regex::new(ip_patterns[0]).unwrap();

    let test_cases = vec![
        ("192.168.1.1", true),
        ("10.0.0.1", true),
        ("255.255.255.255", true),
        ("0.0.0.0", true),
        ("256.1.1.1", false), // Invalid octet
        ("192.168.1", false), // Incomplete
        ("not.an.ip.address", false),
    ];

    for (ip, should_match) in test_cases {
        let matches = re.is_match(ip);
        assert_eq!(matches, should_match, "IP '{}' match result incorrect", ip);
    }
}
