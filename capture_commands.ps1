# PowerShell script to execute all 15 commands and capture output
Set-Location "C:\Users\silverfang\epiwatch"

$commands = @(
    @{ num = 1; cmd = 'git --no-pager status' },
    @{ num = 2; cmd = 'git add .' },
    @{ num = 3; cmd = 'git --no-pager commit -m "feat: initial project scaffold with CI pipeline" --author "Copilot <223556219+Copilot@users.noreply.github.com>"' },
    @{ num = 4; cmd = 'git --no-pager branch data-pipeline' },
    @{ num = 5; cmd = 'git --no-pager branch modeling' },
    @{ num = 6; cmd = 'git --no-pager branch dashboard' },
    @{ num = 7; cmd = 'git --no-pager branch risk-map' },
    @{ num = 8; cmd = 'git --no-pager push origin data-pipeline' },
    @{ num = 9; cmd = 'git --no-pager push origin modeling' },
    @{ num = 10; cmd = 'git --no-pager push origin dashboard' },
    @{ num = 11; cmd = 'git --no-pager push origin risk-map' },
    @{ num = 12; cmd = 'git --no-pager checkout main' },
    @{ num = 13; cmd = 'git --no-pager checkout data-pipeline' },
    @{ num = 14; cmd = 'git --no-pager status --short' },
    @{ num = 15; cmd = 'git --no-pager rev-parse --abbrev-ref HEAD' }
)

$results = @()

foreach ($item in $commands) {
    $num = $item.num
    $cmd = $item.cmd
    
    Write-Host "[COMMAND $num/15]" -ForegroundColor Cyan
    Write-Host "Command: $cmd"
    
    $output = @()
    $exitCode = 0
    
    try {
        $output = Invoke-Expression "& $cmd" 2>&1
        $exitCode = $LASTEXITCODE
    }
    catch {
        $output = $_.Exception.Message
        $exitCode = 1
    }
    
    $results += [PSCustomObject]@{
        Number = $num
        Command = $cmd
        Output = ($output -join "`n")
        ExitCode = $exitCode
    }
    
    Write-Host "Exit Code: $exitCode"
    Write-Host "Output:"
    if ($output) {
        Write-Host ($output -join "`n")
    }
    Write-Host ""
}

# Display summary
Write-Host "========================================"
Write-Host "COMPLETE RESULTS"
Write-Host "========================================"
foreach ($result in $results) {
    Write-Host ""
    Write-Host "COMMAND $($result.Number): $($result.Command)" -ForegroundColor Yellow
    Write-Host "Exit Code: $($result.ExitCode)"
    Write-Host "Output:"
    Write-Host "---"
    Write-Host $result.Output
    Write-Host "---"
}

Write-Host ""
Write-Host "========================================"
Write-Host "FINAL SUMMARY"
Write-Host "========================================"
Write-Host "Current Branch: $($results[14].Output)"
Write-Host "Status Output (Command 14): $($results[13].Output)"
