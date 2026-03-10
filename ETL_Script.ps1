
# param(
#     [Parameter(Mandatory=$true)][string[]]$srcFile,
#     [Parameter(Mandatory=$true)][string[]]$OutputPath,
#     [Parameter(Mandatory=$true)][string]$Delimiter,
#     [Parameter(Mandatory=$true)][int[]]$AmountPosition = @()
# )
[string[]]$srcPath        = 'C:\Users\kimch\iCloudDrive\Documents\Github\PowerShell'
[string[]]$srcFilePattern = 'sourceEx*'
[string[]]$OutputPath     = 'C:\Users\kimch\iCloudDrive\Documents\Github\PowerShell'
[string[]]$OutputFile     = 'output.txt'
[string]$Delimiter        = ''
[string]$lookupFile       = ''
[int[]]$AmountPosition    = @()
    $global:myExitCode    = 0;
    $global:myExitCode    = 0;

function healthCheck {
    Get-Volume | % {
        if($_.DriveLetter -ne $null) {
            $currentStorage = [math]::Round($_.SizeRemaining/1GB, 2);
            $totalStorage   = [math]::Round($_.Size/1GB, 2);
            $currentMemory  = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB, 2);
            $totalMemory    = [math]::Round((Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize/1MB, 2);

            write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ----  Health check start for $($_.DriveLetter.ToString()) drive";
            write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Total storage: $totalStorage GB total";
            write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Free  storage: $currentStorage GB total";
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
}

function fileExists {
    param([string[]]$srcFile)
    # Find the files (error if none found)
    $srcPathsObj = Get-ChildItem -Path $srcFile -ErrorAction SilentlyContinue;
     if ($srcPathsObj.Count -eq 0) {
        throw "No files found matching: $srcFile";
    }
    Write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- $($srcPathsObj.Count) File(s) found";

    foreach ($file in $srcPathsObj) {
        if (Test-Path $file) {
            Write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File found: $($file.Name)";
        }
    }
    return $srcPathsObj
}

function checkDuplicate {
    param([string[]]$currFile)
    $hash = (Get-FileHash $currFile -Algorithm SHA256).Hash;
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Hash: $hash";
    # compare against a db or a file of known hashes to check for duplicates
}

function fileProcess {
    param(
        $currFileObj,
        [string]$lookupFile,
        [string]$Output,
        [string]$Delimiter,
        [int[]]$AmountPosition
    )
    
    $tmpFile = "$($currFileObj.DirectoryName + '\' + $currFileObj.BaseName).tmp"
    write-host $tmpFile
    # $rowCount = 0
    # $totalAmount = 0
    # $seenHashes = @{}
    
    # try {
    #     $reader = [System.IO.File]::OpenText($Source)
    #     $writer = [System.IO.File]::CreateText($tmpFile)
        
    #     while ($null -ne ($line = $reader.ReadLine())) {
    #         $hash = [System.Security.Cryptography.SHA256]::ComputeHash([System.Text.Encoding]::UTF8.GetBytes($line)) -join ''
            
    #         if ($seenHashes.ContainsKey($hash)) {
    #             Write-Warning "Duplicate row skipped (hash: $hash)"
    #             continue
    #         }
            
    #         $seenHashes[$hash] = $true
    #         $writer.WriteLine($line)
    #         $rowCount++
            
    #         if ($AmountPos.Count -gt 0) {
    #             $fields = $line -split [regex]::Escape($Delimiter)
    #             foreach ($pos in $AmountPos) {
    #                 if ($pos -lt $fields.Count -and [decimal]::TryParse($fields[$pos], [ref]$null)) {
    #                     $totalAmount += [decimal]$fields[$pos]
    #                 }
    #             }
    #         }
    #     }
        
    #     $writer.Close()
    #     $reader.Close()
        
    #     Write-Host "✓ File processed: $rowCount rows, Total amount: $totalAmount"
    #     Move-Item $tmpFile $Output -Force
    # }
    # catch {
    #     if ($writer) { $writer.Close() }
    #     if ($reader) { $reader.Close() }
    #     Remove-Item $tmpFile -ErrorAction SilentlyContinue
    #     throw $_
    # }
}

try {
    # Main script execution
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Machine health check: Start" -ForegroundColor Cyan;
    healthCheck;
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Machine health check: Completed" -ForegroundColor Cyan;

    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File existence check: Start" -ForegroundColor Cyan;
    $srcPathsObj = fileExists "$srcPath\$srcFilePattern";
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File existence check: Completed" -ForegroundColor Cyan;

    # Process each file
    $srcPathsObj | ForEach-Object { 
        $currFileObj = $_;
        write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File duplicate check: Start" -ForegroundColor Cyan;
        Write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File: $($currFileObj.Name)";
        checkDuplicate $($currFileObj.FullName);
        write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File duplicate check: Completed" -ForegroundColor Cyan;

        write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File processing (ETL) check: Start" -ForegroundColor Cyan;
        fileProcess $currFileObj $lookupFile $OutputPath $Delimiter $AmountPosition;
        write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File processing (ETL) check: Completed" -ForegroundColor Cyan;
    }
}
catch {
    [System.String]($_.Exception.GetType().FullName, $_.Exception.Message) | write-Error;
    $global:myExitCode = 1;
}
finally {
    # exit $global:myExitCode;
}


