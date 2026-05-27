use schemars::{schema::RootSchema, schema_for};
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use std::{env, fs, path::Path};
use watershed_contracts::{
    ClaimKind, Deposit, FileClaim, Policy, PressureTest, RecoveredIntent, RollbackSpec,
    VerificationSpec, WorkClass,
};

type XtaskResult<T> = Result<T, Box<dyn std::error::Error>>;

fn main() -> XtaskResult<()> {
    let mut args = env::args();
    let program = args.next().unwrap_or_else(|| "xtask".to_owned());
    match args.next().as_deref() {
        Some("schemas") => emit_schemas(),
        Some(command) => Err(format!("unknown xtask command '{command}'").into()),
        None => Err(format!("usage: {program} schemas").into()),
    }
}

fn emit_schemas() -> XtaskResult<()> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .ok_or("xtask crate has no workspace parent")?;
    let schema_dir = root.join("schemas");
    fs::create_dir_all(&schema_dir)?;

    for target in schema_targets()? {
        let path = schema_dir.join(format!("{}.json", target.name));
        fs::write(path, target.contents)?;
    }

    Ok(())
}

struct SchemaTarget {
    name: &'static str,
    contents: String,
}

fn schema_targets() -> XtaskResult<Vec<SchemaTarget>> {
    Ok(vec![
        schema_target("RecoveredIntent", schema_for!(RecoveredIntent))?,
        schema_target("WorkClass", schema_for!(WorkClass))?,
        schema_target("FileClaim", schema_for!(FileClaim))?,
        schema_target("ClaimKind", schema_for!(ClaimKind))?,
        schema_target("VerificationSpec", schema_for!(VerificationSpec))?,
        schema_target("RollbackSpec", schema_for!(RollbackSpec))?,
        schema_target("Policy", schema_for!(Policy))?,
        schema_target("PressureTest", schema_for!(PressureTest))?,
        schema_target("Deposit", schema_for!(Deposit))?,
    ])
}

fn schema_target(name: &'static str, schema: RootSchema) -> XtaskResult<SchemaTarget> {
    let payload = serde_json::to_value(schema)?;
    let hash_input = serde_json::to_vec(&payload)?;
    let hash = Sha256::digest(hash_input);
    let with_comment = with_comment(payload, format!("{name} schema content sha256 {hash:x}"))?;
    let contents = serde_json::to_string_pretty(&with_comment)?;

    Ok(SchemaTarget {
        name,
        contents: format!("{contents}\n"),
    })
}

fn with_comment(payload: Value, comment: String) -> XtaskResult<Value> {
    let Value::Object(fields) = payload else {
        return Err("schema root was not a JSON object".into());
    };

    let mut commented = Map::new();
    commented.insert("$comment".to_owned(), Value::String(comment));
    for (key, value) in fields {
        commented.insert(key, value);
    }

    Ok(Value::Object(commented))
}
