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
        ("AB-12-34-56-C", true),
        ("AB.12.34.56.C", true),
        ("AB 123 456 C", true),
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
fn test_nino_suffix_matches_space_and_letter_or_neither() {
    let nino_patterns = get_patterns_by_name(&["nino"]);
    let re = regex::RegexBuilder::new(nino_patterns[0])
        .case_insensitive(true)
        .build()
        .unwrap();

    let test_cases = vec![
        ("AB123456A", "AB123456A"),
        ("AB123456 A", "AB123456 A"),
        ("AB123456  A", "AB123456  A"),
        ("AB123456 A.", "AB123456 A"),
        // No suffix: trailing space is not part of the match
        ("AB123456 y", "AB123456"),
        // A word starting with a-d is not a suffix letter
        ("AB123456 and more", "AB123456"),
        // An attached suffix letter is always matched
        ("AB123456Cxyz", "AB123456C"),
        ("AB123456.", "AB123456"),
        ("AB123456 And more", "AB123456"),
        // Lower case
        ("ab123456a", "ab123456a"),
        ("ab123456 a", "ab123456 a"),
        ("ab123456  a", "ab123456  a"),
        ("ab123456 a.", "ab123456 a"),
        ("ab123456 y", "ab123456"),
        ("ab123456 and more", "ab123456"),
        ("ab123456cxyz", "ab123456c"),
        ("ab123456.", "ab123456"),
        // Mixed case
        ("Ab123456c", "Ab123456c"),
        ("aB123456 C", "aB123456 C"),
        ("Ab123456 D.", "Ab123456 D"),
    ];

    for (text, expected) in test_cases {
        let found = re.find(text).map(|m| m.as_str());
        assert_eq!(found, Some(expected), "NINO match in '{}' incorrect", text);
    }
}

#[test]
fn test_nino_case_sensitive_requires_upper_case() {
    let nino_patterns = get_patterns_by_name(&["nino"]);
    let re = regex::Regex::new(nino_patterns[0]).unwrap();

    // Lower-case prefix: no match at all
    assert_eq!(re.find("ab123456a"), None);
    // Upper-case prefix with a lower-case suffix: the suffix is not matched
    assert_eq!(re.find("AB123456 a").map(|m| m.as_str()), Some("AB123456"));
    assert_eq!(re.find("AB123456a").map(|m| m.as_str()), Some("AB123456"));
}

#[test]
fn test_nino_separators_and_groupings_match_whole() {
    let nino_patterns = get_patterns_by_name(&["nino"]);
    let re = regex::RegexBuilder::new(nino_patterns[0])
        .case_insensitive(true)
        .build()
        .unwrap();

    let test_cases = vec![
        ("x AB-12-34-56-C y", "AB-12-34-56-C"),
        ("x AB.12.34.56.C y", "AB.12.34.56.C"),
        ("x AB 123 456 C y", "AB 123 456 C"),
        ("x AB 123 456C y", "AB 123 456C"),
        ("x AB123 456 y", "AB123 456"),
        ("x AB-123-456-C y", "AB-123-456-C"),
        ("x ab-12-34-56-c y", "ab-12-34-56-c"),
        ("x ab 123 456 c y", "ab 123 456 c"),
        // Mixed separators
        ("x AB 12-34.56 C y", "AB 12-34.56 C"),
    ];

    for (text, expected) in test_cases {
        let found = re.find(text).map(|m| m.as_str());
        assert_eq!(found, Some(expected), "NINO match in '{}' incorrect", text);
    }
}

#[test]
fn test_nino_does_not_match_inside_phone_numbers() {
    let nino_patterns = get_patterns_by_name(&["nino"]);
    let re = regex::RegexBuilder::new(nino_patterns[0])
        .case_insensitive(true)
        .build()
        .unwrap();

    // Allowing separators between any digits would match e.g. "ll 07700 9"
    for text in [
        "call 07700 900123",
        "Tel 01234 567890",
        "tel 020 7946 0958",
        "call 01632 960 001",
    ] {
        assert_eq!(re.find(text), None, "NINO matched in '{}'", text);
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
        ("SW1A1AA", true),
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
fn test_postcode_any_whitespace_matches_whole() {
    let postcode_patterns = get_patterns_by_name(&["postcode"]);
    let re = regex::Regex::new(postcode_patterns[0]).unwrap();

    let test_cases = vec![
        ("x SW1A1AA y", "SW1A1AA"),
        ("x SW1A 1AA y", "SW1A 1AA"),
        ("x SW1A  1AA y", "SW1A  1AA"),
        ("x SW1A   1AA y", "SW1A   1AA"),
        ("x SW1A\t1AA y", "SW1A\t1AA"),
        ("x SW1A\n1AA y", "SW1A\n1AA"),
        ("x SW1A\r\n1AA y", "SW1A\r\n1AA"),
        ("x M1  1AA y", "M1  1AA"),
    ];

    for (text, expected) in test_cases {
        let found = re.find(text).map(|m| m.as_str());
        assert_eq!(
            found,
            Some(expected),
            "Postcode match in '{}' incorrect",
            text.escape_debug()
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

#[test]
fn test_ipv6_forms_match_whole() {
    let ip_patterns = get_patterns_by_name(&["ip_address"]);
    let re = regex::Regex::new(ip_patterns[1]).unwrap();

    let test_cases = vec![
        // Full 8-group form
        (
            "x 2001:0db8:85a3:0000:0000:8a2e:0370:7334 y",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        ),
        (
            "x 2001:DB8:85A3:0:0:8A2E:370:7334 y",
            "2001:DB8:85A3:0:0:8A2E:370:7334",
        ),
        // "::" compressed: middle, leading, trailing
        ("x 2001:db8::1 y", "2001:db8::1"),
        ("x 2001:db8:0:0:1::1 y", "2001:db8:0:0:1::1"),
        ("x ::1 y", "::1"),
        ("x ::ffff:abcd y", "::ffff:abcd"),
        ("x fe80:: y", "fe80::"),
        ("x 2001:db8:: y", "2001:db8::"),
        ("::", "::"),
        // Embedded IPv4
        ("x ::ffff:192.168.1.1 y", "::ffff:192.168.1.1"),
        ("x ::192.168.1.1 y", "::192.168.1.1"),
        ("x 64:ff9b::192.0.2.33 y", "64:ff9b::192.0.2.33"),
        (
            "x 0:0:0:0:0:ffff:192.168.1.1 y",
            "0:0:0:0:0:ffff:192.168.1.1",
        ),
        // Zone IDs
        ("x fe80::1%eth0 y", "fe80::1%eth0"),
        (
            "x fe80::1ff:fe23:4567:890a%3 y",
            "fe80::1ff:fe23:4567:890a%3",
        ),
        // Bracketed with a port: the address inside is matched
        ("http://[2001:db8::1]:8080/", "2001:db8::1"),
        // Surrounded by punctuation
        ("(2001:db8::1),", "2001:db8::1"),
        ("from 2001:db8::1.", "2001:db8::1"),
        // Directly after a non-ASCII letter
        ("é2001:db8::1", "2001:db8::1"),
    ];

    for (text, expected) in test_cases {
        let found = re.find(text).map(|m| m.as_str());
        assert_eq!(found, Some(expected), "IPv6 match in '{}' incorrect", text);
    }
}

#[test]
fn test_ipv6_does_not_match_times_or_code() {
    let ip_patterns = get_patterns_by_name(&["ip_address"]);
    let re = regex::RegexBuilder::new(ip_patterns[1])
        .case_insensitive(true)
        .build()
        .unwrap();

    for text in [
        "at 12:30:45 today",
        "at 2024-01-01T12:30:45Z",
        "MAC 00:1a:2b:3c:4d:5e",
        "use crate::fmt;",
        "std::io::Result",
        "Foo::Bar::baz()",
        "ratio 1:2:3",
    ] {
        assert_eq!(re.find(text), None, "IPv6 matched in '{}'", text);
    }
}
