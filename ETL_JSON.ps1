function healthCheck {
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ======== Machine health check Start ========" -ForegroundColor Cyan;
    Get-Volume | ForEach-Object {
        if($null -ne $_.DriveLetter) {
            $currentStorage = [math]::Round($_.SizeRemaining/1GB, 2);
            $totalStorage   = [math]::Round($_.Size/1GB, 2);
            $currentMemory  = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB, 2);
            $totalMemory    = [math]::Round((Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize/1MB, 2);

            write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Health check start for $($_.DriveLetter.ToString()) drive";
            write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Total storage: $totalStorage GB total";
            write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Free storage: $currentStorage GB total";
            if($($totalStorage - $currentStorage) -lt ($totalStorage * 0.1)) {
                write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Warning: Low disk space on drive $($_.DriveLetter.ToString())" -ForegroundColor Yellow;
            }
            write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Total memory: $totalMemory GB total";
            write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Free memory: $currentMemory GB total";
            if($($totalMemory - $currentMemory) -lt ($totalMemory * 0.1)) {
                write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Warning: Low memory on drive $($_.DriveLetter.ToString())" -ForegroundColor Yellow;
            }
            write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Health check passed for $($_.DriveLetter.ToString()) drive";
        }
    }
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ======== Machine health check Completed ========" -ForegroundColor Cyan;
}

function jsonETL_initialization {
    # Read ETL configuration from JSON file
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ======== JSON file import started ========" -ForegroundColor Cyan;
    $global:configPath = "C:\Users\kimch\iCloudDrive\Documents\Github\PowerShell\mapping.json";
    if(Test-Path $configPath) {
        write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Configuration file found: $configPath" -ForegroundColor Green;
    } else {
        throw "FATAL ERROR: Configuration file not found at path: $configPath";
    }
    $global:config = Get-Content -Raw $configPath | ConvertFrom-Json;

    # Extract json data
    $global:srcFile      = $global:config.settings.input_file
    $global:srcDelimiter = $global:config.settings.input_file_delimiter
    $global:srcHeader    = $global:config.settings.input_file_has_header
    $global:srcEncoding  = $global:config.settings.input_file_encoding
    $global:opFile       = $global:config.settings.output_file
    $global:opDelimiter  = $global:config.settings.output_file_delimiter
    $global:opHeader     = $global:config.settings.output_file_has_header
    $global:opEncoding   = $global:config.settings.output_file_encoding
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Source file: $srcFile"
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Source delimiter: $srcDelimiter"
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Source header: $srcHeader"
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Source encoding: $srcEncoding"
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Output file: $opFile"
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Output delimiter: $opDelimiter"
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Output header: $opHeader"
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Output encoding: $opEncoding"
    # validate all required configuration values are present
    if (-not ($srcFile -and $srcDelimiter -and $srcHeader -and $srcEncoding -and $opFile -and $opDelimiter -and $opHeader -and $opEncoding)) {
        throw "FATAL ERROR: One or more required configuration values are missing. Please check the JSON file."
    }

    # Check if source file exists
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File existence check started"
    $global:srcFile = Get-ChildItem -Path $srcFile;
    if ($srcFile.Count -gt 1) {
        throw "FATAL ERROR: Multiple source files found.";
    }
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File existence check completed"
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ======== JSON file import completed ========" -ForegroundColor Green;
}

healthCheck
jsonETL_initialization

# begin memory-efficient ETL processing
write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ======== File processing started ========" -ForegroundColor Cyan;

# open input stream reader and output stream writer using configured encodings
try {
    $inputEncodingObj  = [System.Text.Encoding]::GetEncoding($srcEncoding)
    $outputEncodingObj = [System.Text.Encoding]::GetEncoding($opEncoding)
    $reader            = [System.IO.StreamReader]::new($srcFile, $inputEncodingObj)
    $writer            = [System.IO.StreamWriter]::new($opFile, $false, $outputEncodingObj)
    $outputCols        = ($config.output_columns)
    $inputCols         = ($config.source_columns)
    if ($opHeader) {
        write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Writing output header";
        
        $writer.WriteLine($outputCols -join $opDelimiter)
    }
    
    $rowCount = 0
    $skipped = $false
    
    while ($null -ne ($line = $reader.ReadLine())) {
        # Skip header row if configured to do so
        if ($srcHeader -and -not $skipped) {
            write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Skipping first input row";
            $skipped = $true
            continue
        }
        
        # parse fields
        $fields = $line -split [regex]::Escape($srcDelimiter)
        
        # Create an array to hold output values, initialized with empty strings based on the number of output columns
        $outputValues = @("") * $config.output_columns.Count

        # Apply transformations based on the rules defined in the JSON configuration
        foreach ($transform in $config.transformations) {
            $value = $null
            switch ($transform.rule_type) {
                'copy' {
                    # find the index of input and output for this column based on json
                    $opidx = $outputCols.IndexOf($transform.output_column)
                    $ipidx = $inputCols.IndexOf($transform.input_column)
                    $value = $fields[$ipidx]
                    if ($transform.format_as -eq 'lowercase') { $value = $value.ToLower() }
                    elseif ($transform.format_as -eq 'uppercase') { $value = $value.ToUpper() }
                    elseif ($transform.format_as -eq 'phone') {
                        $phoneNumber = ""
                        for (($i = 0), ($j=0); $i -lt $transform.format_pattern.Length; $i++) {
                            if ($transform.format_pattern[$i] -eq '#') { 
                                $phoneNumber += $value[$j]
                                $j++
                            }
                            else {
                                $phoneNumber += $transform.format_pattern[$i]
                            }
                        }
                        $value = $phoneNumber
                    }
                    elseif ($transform.format_as -eq 'date') {
                            if ($transform.input_date_format) {
                                $date = [datetime]::ParseExact($value, $transform.input_date_format, $null)
                            } else {
                                $date = [datetime]::Parse($value)
                            }
                            $value = $date.ToString($transform.format_pattern)
                    }
                    $outputValues[$opidx] = $value
                }
                'combine' {
                    $parts = @()
                    foreach ($col in $transform.input_columns) {
                        $opidx = $outputCols.IndexOf($transform.output_column)
                        $ipidx = $inputCols.IndexOf($col)
                        $parts += $fields[$ipidx]
                    }
                    $value = ($parts -join $transform.join_with)
                    $outputValues[$opidx] = $value
                }
                'calculate' {
                    # find the index of input and output for this column based on json
                    $opidx = $outputCols.IndexOf($transform.output_column)
                    $ipidx = $inputCols.IndexOf($transform.input_column)
                    [decimal]$num = $fields[$ipidx]
                    if ($transform.operation -eq 'multiply') { 
                        $value = [math]::Round($num * $transform.by_value, $transform.round_to_decimals)
                    }
                    elseif ($transform.operation -eq 'add') { 
                        $value = [math]::Round($num + $transform.by_value, $transform.round_to_decimals)
                    }
                    elseif ($transform.operation -eq 'subtract') { 
                        $value = [math]::Round($num - $transform.by_value, $transform.round_to_decimals)
                    }
                    $outputValues[$opidx] = $value
                }
                'fixed' { 
                    $opidx = $outputCols.IndexOf($transform.output_column)
                    $value = $transform.value 
                    $outputValues[$opidx] = $value
                }
                # 'if_then' {
                #     $idx = $sourceIndexMap[$transform.input_column]
                #     [decimal]$chk = $fields[$idx]
                #     $value = $transform.otherwise_use
                #     foreach ($rule in $transform.rules) {
                #         $cond = switch ($rule.if_value) {
                #             'greater_than' { $chk -gt $rule.compare_to }
                #             'less_than'    { $chk -lt $rule.compare_to }
                #             'equals'       { $chk -eq $rule.compare_to }
                #             'greater_equal'{ $chk -ge $rule.compare_to }
                #             'less_equal'   { $chk -le $rule.compare_to }
                #         }
                #         if ($cond) { $value = $rule.then_use; break }
                #     }
                # }
            }
        }
        $rowCount++
        # write the transformed row immediately
        $writer.WriteLine(($outputValues -join $opDelimiter))
        
        # if ($rowCount % 1000 -eq 0) { 
            # write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Processed $rowCount rows" 
        # }
    }
    
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Total rows processed: $rowCount" -ForegroundColor Green
}
catch {
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Error during file processing $rowCount : $($_.Exception.Message)" -ForegroundColor Red
}
finally { 
    if ($reader) { $reader.Close() }
    if ($writer) { $writer.Close() }
}
# write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ======== File processing completed ========" -ForegroundColor Green;
