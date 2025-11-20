@echo off
echo Adding changes to git...
git add hmm/hmm_market_data_collector.py
echo.
echo Committing changes...
git commit -m "feat: Enhance HMM data collector with whale activity detection

- Add comprehensive whale activity detection using Z-score and IQR analysis
- Include max_priority_fee_gwei metric for quantifying jump bids
- Add hourly_volume_percentage_of_total for activity significance
- Implement outlier_detected flag for anomalous gas price behavior  
- Fix indentation issues in gas stats calculation
- Update CSV headers with new whale detection metrics
- Add proper error handling and logging throughout

This enables HMM models to distinguish between:
- High volatility + high volume (profitable for LP)
- High volatility + low volume (dangerous for LP)  
- Normal activity vs whale-driven market movements"

echo.
echo Current git status:
git status --short
echo.
echo Done!
pause
