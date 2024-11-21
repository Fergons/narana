from pathlib import Path
import zipfile
import argparse
import yaml

def create_dataset_structure(dir: str | Path) -> None:
    """
    Build the dataset directory structure as specified in the configuration.
    Args:
        config_path (str | Path): Path to the configuration file.
    Returns:
        TVTropesConfig: The configuration object with defaults applied if necessary.
    """
    dataset_dir = Path(dir) / "tvtropes"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    config_path = dataset_dir / "config.yaml"
    config = {
        "dataset_dir": str(dataset_dir.absolute()),
        "csv_dir":  str(dataset_dir.absolute()),
        "documents_dir":  str((dataset_dir / "docs").absolute()),
        "download_url": None,
        "doc_zip_path": None,
        "csv_zip_path": None
    }
    
    # Create dataset_dir, csv_dir, and documents_dir if they do not exist
    Path(config['dataset_dir']).mkdir(parents=True, exist_ok=True)
    Path(config['csv_dir']).mkdir(parents=True, exist_ok=True)
    Path(config['documents_dir']).mkdir(parents=True, exist_ok=True)
    
    if config["doc_zip_path"] is not None:
        with zipfile.ZipFile(config["doc_zip_path"], 'r') as zip_ref:
            zip_ref.extractall(config["documents_dir"])
    if config["csv_zip_path"] is not None:
        with zipfile.ZipFile(config["csv_zip_path"], 'r') as zip_ref:
            zip_ref.extractall(config["csv_dir"])
    
    with config_path.open('w') as f:
        yaml.dump({"tvtropes": config}, f)

     # TODO: download from source by download url


# TODO: create snapshot of the dataset and zip it to a package
def package_dataset(config_path: str | Path):
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create TV Tropes dataset structure.")
    parser.add_argument("--setup", action="store_true", help="Create dataset structure.")
    parser.add_argument("--dir", type=str, default="./data", help="Path to directory to create dataset structure in.")
    args = parser.parse_args()
    if args.setup:
        create_dataset_structure(args.dir)


