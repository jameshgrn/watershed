use std::path::PathBuf;

#[test]
fn constitutional_violations_do_not_compile() {
    let tests = trybuild::TestCases::new();
    let pattern = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("tests")
        .join("compile_fail")
        .join("*.rs")
        .to_string_lossy()
        .into_owned();

    tests.compile_fail(&pattern);
}
