# Arbitrage Bot Test Script
Write-Host "=== TRIANGULAR ARBITRAGE BOT TEST ===" -ForegroundColor Green

try {
    # 1. Start the system
    Write-Host "`n1. STARTING SYSTEM..." -ForegroundColor Yellow
    $startResult = Invoke-RestMethod -Uri "http://localhost:8000/api/system/control/" -Method POST -ContentType "application/json" -Body '{"action": "start"}'
    Write-Host "   Status: $($startResult.status)" -ForegroundColor Green
    Write-Host "   Message: $($startResult.message)" -ForegroundColor White

    # 2. System Status
    Write-Host "`n2. SYSTEM STATUS..." -ForegroundColor Yellow
    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/system/status/" -Method GET
    Write-Host "   System: $($status.status)" -ForegroundColor Green
    Write-Host "   Opportunities: $($status.opportunities_count)" -ForegroundColor White
    Write-Host "   Health Score: $($status.health_score)/100" -ForegroundColor White

    # 3. Get Opportunities
    Write-Host "`n3. ARBITRAGE OPPORTUNITIES..." -ForegroundColor Yellow
    $opportunities = Invoke-RestMethod -Uri "http://localhost:8000/api/opportunities/" -Method GET
    Write-Host "   Found: $($opportunities.count) opportunities" -ForegroundColor Green
    
    foreach ($opp in $opportunities.opportunities) {
        $triangleStr = $opp.triangle -join ' -> '
        Write-Host "   Triangle: $triangleStr" -ForegroundColor White
        Write-Host "   Profit: $($opp.profit_percentage)%" -ForegroundColor Cyan
    }

    # 4. Execute Trade on the best opportunity
    if ($opportunities.count -gt 0) {
        Write-Host "`n4. EXECUTING TRADE..." -ForegroundColor Yellow
        $bestTriangle = $opportunities.opportunities[0].triangle
        $tradeBody = @{
            triangle = $bestTriangle
            amount = 10
            exchange = "binance"
        } | ConvertTo-Json

        $tradeResult = Invoke-RestMethod -Uri "http://localhost:8000/api/trading/execute/" -Method POST -ContentType "application/json" -Body $tradeBody
        Write-Host "   Trade ID: $($tradeResult.trade_id)" -ForegroundColor White
        Write-Host "   Status: $($tradeResult.status)" -ForegroundColor Green
        Write-Host "   Profit: $$($tradeResult.profit)" -ForegroundColor Cyan
    }

    # 5. Trade History
    Write-Host "`n5. TRADE HISTORY..." -ForegroundColor Yellow
    $history = Invoke-RestMethod -Uri "http://localhost:8000/api/trading/history/" -Method GET
    Write-Host "   Total Trades: $($history.total_trades)" -ForegroundColor White
    Write-Host "   Total Profit: $$($history.total_profit)" -ForegroundColor Cyan

    # 6. Performance
    Write-Host "`n6. PERFORMANCE METRICS..." -ForegroundColor Yellow
    $performance = Invoke-RestMethod -Uri "http://localhost:8000/api/performance/" -Method GET
    Write-Host "   Total Profit: $$($performance.totalProfit)" -ForegroundColor Green
    Write-Host "   Trades Today: $($performance.tradesToday)" -ForegroundColor White
    Write-Host "   Success Rate: $($performance.successRate)%" -ForegroundColor Cyan

    # 7. Health Check
    Write-Host "`n7. HEALTH CHECK..." -ForegroundColor Yellow
    $health = Invoke-RestMethod -Uri "http://localhost:8000/api/health/" -Method GET
    Write-Host "   Overall Status: $($health.status)" -ForegroundColor Green
    Write-Host "   System Running: $($health.system_running)" -ForegroundColor White

    Write-Host "`n=== TEST COMPLETED SUCCESSFULLY ===" -ForegroundColor Green

} catch {
    Write-Host "`nERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure the Django server is running on http://localhost:8000" -ForegroundColor Yellow
}