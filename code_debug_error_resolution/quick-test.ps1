# Quick test to verify solution still works with all changes

$taskDir = $PSScriptRoot

Write-Host "`n=== Testing Solution with Updated Code ===" -ForegroundColor Cyan

# Build and test
docker build -t debug-test -f "$taskDir/environment/Dockerfile" "$taskDir/environment/" 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

# Apply solution and commit
$containerId = docker run -d debug-test bash -c "bash /solution/solve.sh && tail -f /dev/null" 2>&1 | Select-Object -Last 1
Start-Sleep -Seconds 3
docker commit $containerId debug-fixed | Out-Null
docker stop $containerId | Out-Null
docker rm $containerId | Out-Null

# Run tests
Write-Host "Running tests..." -ForegroundColor Cyan
docker run --rm -v "${taskDir}/tests:/tests:ro" -v "${taskDir}/solution:/solution:ro" debug-fixed bash /tests/test.sh

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Tests failed!" -ForegroundColor Red
}

# Cleanup
docker rmi debug-fixed -f 2>&1 | Out-Null
docker rmi debug-test -f 2>&1 | Out-Null
