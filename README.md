# ETL_JSON.ps1

A PowerShell script for performing ETL (Extract, Transform, Load) operations on JSON data using a customizable mapping file.

## Features

- **Extract**: Reads JSON data from a source file.
- **Transform**: Applies transformations based on rules defined in `mapping.json`.
- **Load**: Outputs the transformed data to a destination file.

## Usage

```powershell
.\ETL_JSON.ps1 mapping.json
```

### Parameters

- `-MappingFile` &mdash; Path to the mapping configuration (`mapping.json`).

## Requirements

- PowerShell 5.1 or later
- `mapping.json` file with transformation rules
- Input JSON data file (source)
- Output JSON data file (destination)

## License

This project is private. All rights reserved. Redistribution or use is not permitted without explicit permission from the author.

---