
# param(
#     [Parameter(Mandatory=$true)][string[]]$SourcePath,
#     [Parameter(Mandatory=$true)][string[]]$OutputPath,
#     [Parameter(Mandatory=$true)][string]$Delimiter,
#     [Parameter(Mandatory=$true)][int[]]$AmountPosition = @()
# )
[string[]]$SourcePath='C:\Users\kimch\iCloudDrive\Documents\Github\PowerShell\sourceEx*'
[string[]]$OutputPath=''
[string]$Delimiter=''
[string]$lookupFlag='Y'
[int[]]$AmountPosition = @()

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
    param([string[]]$SourcePath)
    # Find the files (error if none found)
    $srcPaths = Get-ChildItem -Path $SourcePath -ErrorAction SilentlyContinue;
     if ($srcPaths.Count -eq 0) {
        throw "No files found matching: $SourcePath";
    }
    Write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- $($srcPaths.Count) File(s) found";

    foreach ($file in $srcPaths) {
        if (Test-Path $file) {
            Write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File found: $file";
        }
    }
    return $srcPaths
}

function checkDuplicate {
    param([string[]]$SourcePath)
    $srcPaths | ForEach-Object { 
        Write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File: $($_.Name)";
        $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash;
        write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Hash: $hash";
        # compare against a db or a file of known hashes to check for duplicates
    }
}

function Process-File {
    # param(
    #     [string]$Source,
    #     [string]$Output,
    #     [string]$Delimiter,
    #     [int[]]$AmountPos
    # )
    
    # $tmpFile = "$Output.tmp"
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

# Main script execution
write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Machine health check: Start" -ForegroundColor Cyan;
healthCheck;
write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Machine health check: Completed" -ForegroundColor Cyan;

write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File existence check: Start" -ForegroundColor Cyan;
$srcPaths = fileExists $SourcePath;
write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File existence check: Completed" -ForegroundColor Cyan;

write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File duplicate check: Start" -ForegroundColor Cyan;
checkDuplicate $srcPaths;
write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File duplicate check: Completed" -ForegroundColor Cyan;

write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File processing (ETL) check: Start" -ForegroundColor Cyan;
write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File processing (ETL) check: Completed" -ForegroundColor Cyan;

# for ($i = 0; $i -lt $SourcePath.Count; $i++) {
#     Write-Host "Processing: $($SourcePath[$i]) -> $($OutputPath[$i])"
#     Process-File $SourcePath[$i] $OutputPath[$i] $Delimiter $AmountPosition
# }

# Write-Host "✓ All files processed successfully"
