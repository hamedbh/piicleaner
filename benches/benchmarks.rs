use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};
use piicleaner::core::{
    clean_pii_with_cleaners_batch_core, detect_pii_with_cleaners_batch_core, Cleaning,
};
use std::hint::black_box;

#[derive(Clone)]
struct TestCase {
    name: String,
    text_data: Vec<String>,
    operation: String,
    ignore_case: bool,
}

fn create_sample_strings() -> Vec<String> {
    vec![
        "My email address is person@example.com".to_string(),
        "Sophie Taylor at 1 High Street, London, W1 2BC".to_string(),
        "Call me at +44 7890 123 456 urgently".to_string(),
        "I am owed a refund in the amount of £1,234.56. I expect payment promptly.".to_string(),
        "My reference number is 1234567890".to_string(),
        "I am Ali Mahmood, my National Insurance number is AB123 456A".to_string(),
        "Here goes: <some-sort-of-tag>".to_string(),
        "The request came from 192.168.0.0".to_string(),
    ]
}

fn create_clean_strings() -> Vec<String> {
    vec![
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.".to_string(),
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.".to_string(),
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco.".to_string(),
        "Duis aute irure dolor in reprehenderit in voluptate velit esse.".to_string(),
        "Excepteur sint occaecat cupidatat non proident, sunt in culpa.".to_string(),
        "Nulla pariatur. At vero eos et accusamus et iusto odio dignissimos.".to_string(),
        "Et harum quidem rerum facilis est et expedita distinctio.".to_string(),
        "Nam libero tempore, cum soluta nobis est eligendi optio cumque.".to_string(),
    ]
}

fn generate_large_list(size: usize, pii_ratio: f32) -> Vec<String> {
    let pii_samples = create_sample_strings();
    let clean_samples = create_clean_strings();
    let pii_count = (size as f32 * pii_ratio) as usize;

    (0..size)
        .map(|i| {
            if i < pii_count {
                let base_string = &pii_samples[i % pii_samples.len()];
                let replacement = i % 10;
                // Modify the strings to include the counter
                base_string
                    .replace("person", &format!("person{}", replacement))
                    .replace("W1 2BC", &format!("W{} 2BC", replacement))
                    .replace("7890", &format!("789{}", replacement))
                    .replace("1,234.56", &format!("1,234.5{}", replacement))
                    .replace("1234567890", &format!("12345678{}0", replacement))
                    .replace("AB123", &format!("AB12{}", replacement))
                    .replace("some-sort", &format!("some{}-sort", replacement))
                    .replace("168.0", &format!("168.{}", replacement))
            } else {
                clean_samples[i % clean_samples.len()].clone()
            }
        })
        .collect()
}

fn create_test_cases() -> Vec<TestCase> {
    let samples = create_sample_strings();

    // For now, let's start with just a few test cases
    let text_types = [
        ("individual", vec![samples[0].clone()]), // Single email string
        ("large_list", generate_large_list(100000, 0.2)), // 100,000 strings
    ];

    let operations = ["detect", "redact", "replace"];
    let case_settings = [false, true];

    let mut test_cases = Vec::new();

    for (text_name, text_data) in text_types {
        for operation in operations {
            for ignore_case in case_settings {
                test_cases.push(TestCase {
                    name: format!("{}_{}_ignore_case_{}", text_name, operation, ignore_case),
                    text_data: text_data.clone(),
                    operation: operation.to_string(),
                    ignore_case,
                });
            }
        }
    }

    test_cases
}

fn benchmark_pii_matrix(c: &mut Criterion) {
    let mut group = c.benchmark_group("pii_operations");

    group.measurement_time(std::time::Duration::from_secs(10));

    for test_case in create_test_cases() {
        group.bench_with_input(
            BenchmarkId::new("matrix", &test_case.name),
            &test_case,
            |b, tc| {
                b.iter(|| match tc.operation.as_str() {
                    "detect" => {
                        let _result = detect_pii_with_cleaners_batch_core(
                            black_box(&tc.text_data),
                            &["all"],
                            black_box(tc.ignore_case),
                        );
                    }
                    "redact" => {
                        let _result = clean_pii_with_cleaners_batch_core(
                            black_box(&tc.text_data),
                            &["all"],
                            Cleaning::Redact,
                            black_box(tc.ignore_case),
                        );
                    }
                    "replace" => {
                        let _result = clean_pii_with_cleaners_batch_core(
                            black_box(&tc.text_data),
                            &["all"],
                            Cleaning::Replace,
                            black_box(tc.ignore_case),
                        );
                    }
                    _ => panic!("Unknown operation: {}", tc.operation),
                })
            },
        );
    }
    group.finish();
}

criterion_group!(benches, benchmark_pii_matrix);
criterion_main!(benches);
