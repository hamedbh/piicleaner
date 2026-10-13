//! Polars expression plugin behind the `.pii` expression namespace and
//! `Cleaner.clean_dataframe()`/`detect_dataframe()`.
//!
//! Polars loads these functions from this extension module and passes whole
//! columns through the Arrow C data interface, so no text is converted to or
//! from Python objects. Rows are processed in parallel with rayon, as in the
//! batch functions.

use polars_arrow::array::ListArray;
use polars_arrow::bitmap::Bitmap;
use polars_arrow::offset::OffsetsBuffer;
use polars_core::prelude::*;
use polars_error::{polars_err, PolarsResult};
use pyo3_polars::derive::polars_expr;
use rayon::prelude::*;
use serde::Deserialize;

use crate::core::{self, Cleaning};
use crate::{check_cleaners, to_char_offsets, DetectionMatch};

#[derive(Deserialize)]
struct CleanKwargs {
    cleaners: Vec<String>,
    cleaning: String,
    ignore_case: bool,
    replace_string: Option<String>,
}

#[derive(Deserialize)]
struct DetectKwargs {
    cleaners: Vec<String>,
    ignore_case: bool,
}

/// Borrow the cleaner names and check them against the registry. The Python
/// side validates when the expression is built; this guards direct use.
fn cleaner_refs(cleaners: &[String]) -> PolarsResult<Vec<&str>> {
    let refs: Vec<&str> = cleaners.iter().map(String::as_str).collect();
    check_cleaners(&refs).map_err(|e| polars_err!(InvalidOperation: "{}", e))?;
    Ok(refs)
}

/// The values of a string column, nulls as `None`
fn str_values(inputs: &[Series]) -> PolarsResult<Vec<Option<&str>>> {
    Ok(inputs[0].str()?.iter().collect())
}

#[polars_expr(output_type=String)]
fn clean_pii(inputs: &[Series], kwargs: CleanKwargs) -> PolarsResult<Series> {
    let cleaning =
        Cleaning::parse(&kwargs.cleaning).map_err(|e| polars_err!(InvalidOperation: "{}", e))?;
    let cleaners = cleaner_refs(&kwargs.cleaners)?;
    let replace_string = kwargs.replace_string.as_deref();

    let cleaned: Vec<Option<String>> = str_values(inputs)?
        .par_iter()
        .map(|text| {
            text.map(|text| {
                core::clean_pii_with_cleaners_core(
                    text,
                    &cleaners,
                    cleaning,
                    kwargs.ignore_case,
                    replace_string,
                )
            })
        })
        .collect();

    Ok(
        StringChunked::from_iter_options(inputs[0].name().clone(), cleaned.into_iter())
            .into_series(),
    )
}

/// One detection match: character offsets, the matched text and its type
fn match_dtype() -> DataType {
    DataType::Struct(vec![
        Field::new("start".into(), DataType::Int64),
        Field::new("end".into(), DataType::Int64),
        Field::new("text".into(), DataType::String),
        Field::new("type".into(), DataType::String),
    ])
}

fn detect_pii_output(input_fields: &[Field]) -> PolarsResult<Field> {
    Ok(Field::new(
        input_fields[0].name().clone(),
        DataType::List(Box::new(match_dtype())),
    ))
}

#[polars_expr(output_type_func=detect_pii_output)]
fn detect_pii(inputs: &[Series], kwargs: DetectKwargs) -> PolarsResult<Series> {
    let cleaners = cleaner_refs(&kwargs.cleaners)?;

    let rows: Vec<Option<Vec<DetectionMatch>>> = str_values(inputs)?
        .par_iter()
        .map(|text| {
            text.map(|text| {
                to_char_offsets(
                    text,
                    core::detect_pii_with_cleaners_core(text, &cleaners, kwargs.ignore_case),
                )
            })
        })
        .collect();

    // Build the list column in one go: flat struct fields for every match,
    // plus offsets marking where each row's matches start. Null rows stay
    // null.
    let n_matches = rows.iter().flatten().map(Vec::len).sum();
    let mut starts: Vec<i64> = Vec::with_capacity(n_matches);
    let mut ends: Vec<i64> = Vec::with_capacity(n_matches);
    let mut texts: Vec<String> = Vec::with_capacity(n_matches);
    let mut types: Vec<String> = Vec::with_capacity(n_matches);
    let mut offsets: Vec<i64> = Vec::with_capacity(rows.len() + 1);
    offsets.push(0);
    let validity: Bitmap = rows.iter().map(Option::is_some).collect();
    for row in rows {
        for (start, end, text, pii_type) in row.into_iter().flatten() {
            starts.push(start as i64);
            ends.push(end as i64);
            texts.push(text);
            types.push(pii_type);
        }
        offsets.push(starts.len() as i64);
    }

    let fields = [
        Series::new("start".into(), starts),
        Series::new("end".into(), ends),
        Series::new("text".into(), texts),
        Series::new("type".into(), types),
    ];
    let values = StructChunked::from_series(PlSmallStr::EMPTY, n_matches, fields.iter())?;
    let values = values.rechunk().chunks()[0].clone();
    let list = ListArray::<i64>::new(
        ListArray::<i64>::default_datatype(values.dtype().clone()),
        OffsetsBuffer::try_from(offsets)?,
        values,
        Some(validity),
    );
    let name = inputs[0].name().clone();
    // SAFETY: the array was built from columns of exactly these types
    let out = unsafe {
        ListChunked::from_chunks_and_dtype(
            name,
            vec![Box::new(list)],
            DataType::List(Box::new(match_dtype())),
        )
    };
    Ok(out.into_series())
}
