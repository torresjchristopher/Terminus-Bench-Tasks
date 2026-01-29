# Test Solution Script
# This builds the environment, applies the solution, then runs tests

$taskDir = $PSScriptRoot

Write-Host "`n=== Building Environment ===" -ForegroundColor Cyan
docker build -t debug-server-test -f "$taskDir/environment/Dockerfile" "$taskDir/environment/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Environment build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Creating Container with Solution Applied ===" -ForegroundColor Cyan
# Run the solution and keep the container
$containerId = docker run -d `
    -v "${taskDir}/solution:/solution:ro" `
    debug-server-test `
    bash -c "bash /solution/solve.sh && tail -f /dev/null"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create container!" -ForegroundColor Red
    exit 1
}

# Wait for solution to complete
Start-Sleep -Seconds 2

Write-Host "`n=== Committing Fixed Version ===" -ForegroundColor Cyan
docker commit $containerId debug-server-fixed | Out-Null

Write-Host "`n=== Stopping Temporary Container ===" -ForegroundColor Cyan
docker stop $containerId | Out-Null
docker rm $containerId | Out-Null

Write-Host "`n=== Running Tests on Fixed Version ===" -ForegroundColor Cyan
docker run --rm `
    -v "${taskDir}/tests:/tests:ro" `
    debug-server-fixed `
    bash /tests/test.sh

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ All tests passed with solution!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Some tests failed!" -ForegroundColor Red
}

# Cleanup
Write-Host "`n=== Cleaning Up ===" -ForegroundColor Cyan
docker rmi debug-server-fixed -f | Out-Null
docker rmi debug-server-test -f | Out-Null
