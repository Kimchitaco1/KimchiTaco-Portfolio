
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
[bool]$header             = $false;
$global:myExitCode        = 0;

function healthCheck {
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ==== Machine health check Start ====" -ForegroundColor Cyan;
    Get-Volume | ForEach-Object {
        if($null -ne $_.DriveLetter) {
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
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ==== Machine health check Completed ====" -ForegroundColor Cyan;
}

function fileExists {
    param([string[]]$srcFile)
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ==== File existence check Start ====" -ForegroundColor Cyan;
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
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ==== File existence check Completed ====" -ForegroundColor Cyan;
    return $srcPathsObj
}

function checkDuplicate {
    param([string[]]$currFile)
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File duplicate check: Start" -ForegroundColor Cyan;
    $hash = (Get-FileHash $currFile -Algorithm SHA256).Hash;
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- Hash: $hash";
    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ---- File duplicate check: Completed" -ForegroundColor Cyan;
}

function fileProcess {
    param(
        $currFileObj,
        [string]$lookupFile,
        [string]$OutputPath,
        [string]$Delimiter,
        [int[]]$AmountPosition
    )
    $fileSize = (Get-Item $currFileObj.FullName).Length;
    $fileSize = [math]::Round($fileSize / 1KB, 2);
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ----  File size: $fileSize KB";
    $rowCount = (Get-Content $currFileObj.FullName | Measure-Object -Line).Lines
    write-host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ----  Row count: $rowCount";

    if ($hasHeader -eq $true) {
        $header = Get-Content $currFileObj.FullName -Head 1
        $header | Out-File "$OutputPath\$OutputFile"
    }
    try {
        $reader = [System.IO.File]::OpenText($currFileObj.FullName)
        $writer = [System.IO.File]::CreateText("$OutputPath\$OutputFile")
        while ($null -ne ($line = $reader.ReadLine())) {
            $hash = [System.Security.Cryptography.SHA256]::ComputeHash([System.Text.Encoding]::UTF8.GetBytes($line)) -join ''
            if ($seenHashes.ContainsKey($hash)) {
                Write-Warning "Duplicate row skipped (hash: $hash `n$line)"
                continue
            }
            $seenHashes[$hash] = $true
            $writer.WriteLine($line)
            $rowCount++
            
            if ($AmountPos.Count -gt 0) {
                $fields = $line -split [regex]::Escape($Delimiter)
                foreach ($pos in $AmountPos) {
                    if ($pos -lt $fields.Count -and [decimal]::TryParse($fields[$pos], [ref]$null)) {
                        $totalAmount += [decimal]$fields[$pos]
                    }
                }
            }
        }
        
        $writer.Close()
        $reader.Close()
        
        Write-Host "✓ File processed: $rowCount rows, Total amount: $totalAmount"
        Move-Item $tmpFile $Output -Force
    }
    catch {
        if ($writer) { $writer.Close() }
        if ($reader) { $reader.Close() }
        Remove-Item $tmpFile -ErrorAction SilentlyContinue
        throw $_
    }

    write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ==== File $($currFileObj.Name) processing Completed ====" -ForegroundColor Cyan;
}

try {
    healthCheck;
    $srcPathsObj = fileExists "$srcPath\$srcFilePattern";
    # Process each file
    $srcPathsObj | ForEach-Object { 
        $currFileObj = $_;
        write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ==== File $($currFileObj.Name) processing Start ====" -ForegroundColor Cyan;
        checkDuplicate $($currFileObj.FullName);
        fileProcess $currFileObj $lookupFile $OutputPath $Delimiter $AmountPosition;
        write-Host "$(Get-Date -UFormat "%m-%d-%Y %R:%S") ==== File $($currFileObj.Name) processing Completed ====" -ForegroundColor Cyan;
    }
}
catch {
    [System.String]($_.Exception.GetType().FullName, $_.Exception.Message) | write-Error;
    $global:myExitCode = 1;
}
finally {
    # exit $global:myExitCode;
}


