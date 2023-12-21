use clap::Parser;
use std::{error::Error, io, io::Write, path::Path};

mod tree;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path and name of the file to read
    #[arg(short, long)]
    file: Option<String>,
}

fn main() -> Result<(), Box<dyn Error>> {
    let args = Args::parse();

    let trees = if let Some(file_path) = args.file {
        load_csv_from_file(&file_path)?
    } else {
        // Check if stdin is being used
        if atty::is(atty::Stream::Stdin) {
            // Stdin is not being used, prompt for file path
            let file_path = prompt_for_file_path()?;
            if !Path::new(&file_path).exists() {
                return Err(format!("File '{}' does not exist.", file_path).into());
            }
            load_csv_from_file(&file_path)?
        } else {
            // Read from stdin
            load_csv_from_stdin()?
        }
    };

    // let species_map = tree::species::load_species_data()?;

    let mut wtr = csv::Writer::from_writer(io::stdout());

    for tree in trees {
        println!("{}", tree.get_gross_stem_volume());
        // wtr.serialize(tree)?;
    }

    wtr.flush()?;

    Ok(())
}

fn prompt_for_file_path() -> Result<String, Box<dyn Error>> {
    print!("Please enter the path to a CSV file: ");
    io::stdout().flush()?; // Ensure the prompt is printed immediately

    let mut path = String::new();
    io::stdin().read_line(&mut path)?;
    Ok(path.trim().to_string())
}

/// Loads tree records from a CSV file at the given path.
/// Returns a vector of `TreeRecord` or an error if the operation fails.
fn load_csv_from_file(path: &str) -> Result<Vec<tree::TreeRecordInput>, csv::Error> {
    let mut rdr = csv::Reader::from_path(path)?;
    let mut trees = Vec::new();
    for result in rdr.deserialize() {
        let tree: tree::TreeRecordInput = result?;
        trees.push(tree);
    }
    Ok(trees)
}

/// Loads tree records from standard input (stdin).
/// Returns a vector of `TreeRecord` or an error if the operation fails.
fn load_csv_from_stdin() -> Result<Vec<tree::TreeRecordInput>, csv::Error> {
    let mut rdr = csv::Reader::from_reader(io::stdin());
    let mut trees = Vec::new();
    for result in rdr.deserialize() {
        let tree: tree::TreeRecordInput = result?;
        trees.push(tree);
    }
    Ok(trees)
}
