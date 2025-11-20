"""
Data Analyzer - Impermanent Loss and P&L Calculations
====================================================

This module contains all the mathematical functions for calculating:
- Impermanent Loss
- Profit & Loss for LP positions
- Position performance analysis

Based on the formulas from impermanent_loss.ipynb

Author: Generated for DeFi-RAG Project
"""

import logging
import math
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone


class ImpermanentLossCalculator:
    """
    Handles all IL and P&L calculations for LP positions.
    
    Based on proven formulas from the DeFi-RAG research notebook.
    """
    
    def __init__(self):
        """Initialize the calculator."""
        self.logger = logging.getLogger(__name__)
    
    def calculate_impermanent_loss(
        self, 
        initial_price_ratio: float, 
        current_price_ratio: float
    ) -> float:
        """
        Calculate Impermanent Loss based on price ratio change.
        
        This is the core function from impermanent_loss.ipynb
        
        Args:
            initial_price_ratio: Initial price ratio (token_a_price / token_b_price)
            current_price_ratio: Current price ratio (token_a_price / token_b_price)
            
        Returns:
            float: IL as decimal (positive value representing loss amount, e.g., 0.05 for 5% IL loss)
        """
        try:
            # Calculate the relative price change
            price_ratio = current_price_ratio / initial_price_ratio
            
            # IL formula: IL = 2 * (sqrt(price_ratio) / (1 + price_ratio)) - 1
            il_raw = 2 * (math.sqrt(price_ratio) / (1 + price_ratio)) - 1
            
            # Convert to financial standard (positive number representing loss amount)
            il_loss_amount = abs(il_raw) if il_raw < 0 else 0.0
            
            self.logger.debug(f"IL calculation: ratio={price_ratio:.4f}, IL_loss={il_loss_amount:.4f}")
            
            return il_loss_amount
            
        except Exception as e:
            self.logger.error(f"Error calculating IL: {e}")
            return 0.0
    
    def calculate_impermanent_loss_percentage(
        self, 
        initial_price_ratio: float, 
        current_price_ratio: float
    ) -> str:
        """
        Calculate IL and return as formatted percentage string.
        
        Args:
            initial_price_ratio: Initial price ratio
            current_price_ratio: Current price ratio
            
        Returns:
            str: Formatted percentage (e.g., "5.72%" for 5.72% loss)
        """
        il = self.calculate_impermanent_loss(initial_price_ratio, current_price_ratio)
        return f"{il:.2%}"
    
    def calculate_lp_position_value(
        self,
        lp_tokens_held: float,
        total_lp_supply: float,
        reserve_a: float,
        reserve_b: float,
        price_a_usd: float,
        price_b_usd: float
    ) -> Dict[str, float]:
        """
        Calculate current value of LP position.
        
        Args:
            lp_tokens_held: Amount of LP tokens held
            total_lp_supply: Total LP token supply
            reserve_a: Token A reserves in pool
            reserve_b: Token B reserves in pool
            price_a_usd: Price of token A in USD
            price_b_usd: Price of token B in USD
            
        Returns:
            Dict with position details
        """
        try:
            if total_lp_supply <= 0:
                return {
                    'total_value_usd': 0.0,
                    'token_a_amount': 0.0,
                    'token_b_amount': 0.0,
                    'token_a_value_usd': 0.0,
                    'token_b_value_usd': 0.0
                }
            
            # Calculate ownership percentage
            ownership_percentage = lp_tokens_held / total_lp_supply
            
            # Calculate token amounts owned
            token_a_amount = reserve_a * ownership_percentage
            token_b_amount = reserve_b * ownership_percentage
            
            # Calculate USD values
            token_a_value_usd = token_a_amount * price_a_usd
            token_b_value_usd = token_b_amount * price_b_usd
            total_value_usd = token_a_value_usd + token_b_value_usd
            
            result = {
                'total_value_usd': total_value_usd,
                'token_a_amount': token_a_amount,
                'token_b_amount': token_b_amount,
                'token_a_value_usd': token_a_value_usd,
                'token_b_value_usd': token_b_value_usd,
                'ownership_percentage': ownership_percentage
            }
            
            self.logger.debug(f"LP position value calculated: ${total_value_usd:.2f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating LP position value: {e}")
            return {
                'total_value_usd': 0.0,
                'token_a_amount': 0.0,
                'token_b_amount': 0.0,
                'token_a_value_usd': 0.0,
                'token_b_value_usd': 0.0,
                'ownership_percentage': 0.0
            }
    
    def calculate_hold_strategy_value(
        self,
        initial_token_a_amount: float,
        initial_token_b_amount: float,
        current_price_a_usd: float,
        current_price_b_usd: float
    ) -> Dict[str, float]:
        """
        Calculate value if tokens were simply held (not in LP).
        
        Args:
            initial_token_a_amount: Initial amount of token A
            initial_token_b_amount: Initial amount of token B
            current_price_a_usd: Current price of token A
            current_price_b_usd: Current price of token B
            
        Returns:
            Dict with hold strategy values
        """
        try:
            token_a_value_usd = initial_token_a_amount * current_price_a_usd
            token_b_value_usd = initial_token_b_amount * current_price_b_usd
            total_value_usd = token_a_value_usd + token_b_value_usd
            
            return {
                'total_value_usd': total_value_usd,
                'token_a_value_usd': token_a_value_usd,
                'token_b_value_usd': token_b_value_usd
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating hold strategy value: {e}")
            return {
                'total_value_usd': 0.0,
                'token_a_value_usd': 0.0,
                'token_b_value_usd': 0.0
            }
    
    def compare_strategies(
        self,
        position_data: Dict[str, Any],
        current_reserves: Dict[str, float],
        current_prices: Dict[str, float],
        estimated_fees_earned: float = 0.0
    ) -> Dict[str, Any]:
        """
        Compare LP strategy vs Hold strategy (like compare() function from notebook).
        
        Args:
            position_data: Initial position data
            current_reserves: Current pool reserves
            current_prices: Current token prices
            estimated_fees_earned: Estimated fees earned from LP
            
        Returns:
            Dict with comparison results
        """
        try:
            # Extract initial data
            initial_token_a = position_data['initial_liquidity_a']
            initial_token_b = position_data['initial_liquidity_b']
            initial_price_a = position_data['initial_price_a_usd']
            initial_price_b = position_data['initial_price_b_usd']
            lp_tokens_held = position_data.get('lp_tokens_held', 0)
            total_lp_supply = current_reserves.get('total_lp_supply', 1)
            
            # Current data
            current_price_a = current_prices['token_a_usd']
            current_price_b = current_prices['token_b_usd']
            reserve_a = current_reserves['reserve_a']
            reserve_b = current_reserves['reserve_b']
            
            # Calculate hold strategy value
            hold_value = self.calculate_hold_strategy_value(
                initial_token_a,
                initial_token_b,
                current_price_a,
                current_price_b
            )
            
            # Calculate LP position value
            lp_value = self.calculate_lp_position_value(
                lp_tokens_held,
                total_lp_supply,
                reserve_a,
                reserve_b,
                current_price_a,
                current_price_b
            )
            
            # Calculate IL
            initial_ratio = initial_price_a / initial_price_b
            current_ratio = current_price_a / current_price_b
            il = self.calculate_impermanent_loss(initial_ratio, current_ratio)
            
            # Calculate P&L
            initial_investment = (initial_token_a * initial_price_a + 
                                initial_token_b * initial_price_b)
            
            hold_pnl = hold_value['total_value_usd'] - initial_investment
            lp_pnl = (lp_value['total_value_usd'] + estimated_fees_earned) - initial_investment
            
            # Determine better strategy
            better_strategy = 'LP' if lp_pnl > hold_pnl else 'Hold'
            
            result = {
                'initial_investment_usd': initial_investment,
                'hold_strategy': {
                    'current_value_usd': hold_value['total_value_usd'],
                    'pnl_usd': hold_pnl,
                    'pnl_percentage': hold_pnl / initial_investment if initial_investment > 0 else 0
                },
                'lp_strategy': {
                    'current_value_usd': lp_value['total_value_usd'],
                    'fees_earned_usd': estimated_fees_earned,
                    'total_value_usd': lp_value['total_value_usd'] + estimated_fees_earned,
                    'pnl_usd': lp_pnl,
                    'pnl_percentage': lp_pnl / initial_investment if initial_investment > 0 else 0
                },
                'impermanent_loss': {
                    'percentage': il,
                    'usd_amount': hold_value['total_value_usd'] - lp_value['total_value_usd']
                },
                'better_strategy': better_strategy,
                'calculation_time': datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(f"Strategy comparison: {better_strategy} is better")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error comparing strategies: {e}")
            return {}
    
    def calculate_price_impact_scenarios(
        self,
        initial_price_ratio: float,
        scenarios: list = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate IL for different price change scenarios.
        
        Args:
            initial_price_ratio: Initial price ratio
            scenarios: List of price multipliers (default: common scenarios)
            
        Returns:
            Dict with IL for each scenario
        """
        if scenarios is None:
            scenarios = [0.5, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0]
        
        results = {}
        
        for multiplier in scenarios:
            new_ratio = initial_price_ratio * multiplier
            il = self.calculate_impermanent_loss(initial_price_ratio, new_ratio)
            
            change_description = f"{multiplier}x"
            if multiplier < 1:
                change_description = f"-{(1-multiplier)*100:.0f}%"
            elif multiplier > 1:
                change_description = f"+{(multiplier-1)*100:.0f}%"
            else:
                change_description = "No change"
            
            results[change_description] = {
                'price_multiplier': multiplier,
                'il_percentage': il,
                'il_formatted': f"{il:.2%}"
            }
        
        return results
    
    def check_alert_thresholds(
        self,
        current_il: float,
        position_config: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Check if current IL crosses any alert thresholds.
        
        Args:
            current_il: Current IL percentage (as decimal, can be negative or positive)
                       Negative values: -0.05 means 5% loss
                       Positive values: 0.05 means 5% loss
            position_config: Position configuration with thresholds
            
        Returns:
            Dict with alert flags
        """
        try:
            threshold = position_config.get('il_alert_threshold', 0.05)  # Default 5%
            
            # Handle both negative and positive IL conventions
            # Convert to absolute loss amount for comparison
            il_loss_amount = abs(current_il)
            
            # Check if absolute IL loss exceeds threshold
            il_alert = il_loss_amount > threshold
            
            return {
                'il_threshold_crossed': il_alert,
                'current_il': current_il,
                'threshold': threshold,
                'severity': self._get_il_severity(il_loss_amount)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking alert thresholds: {e}")
            return {
                'il_threshold_crossed': False,
                'current_il': 0.0,
                'threshold': 0.05,
                'severity': 'none'
            }
    
    def _get_il_severity(self, il: float) -> str:
        """
        Get IL severity level.
        
        Args:
            il: IL percentage as positive decimal (0.05 for 5% loss)
                Should always be positive (absolute value)
            
        Returns:
            str: Severity level
        """
        # Ensure we work with absolute value
        il_abs = abs(il)
        
        if il_abs < 0.02:  # < 2%
            return 'low'
        elif il_abs < 0.05:  # < 5%
            return 'medium'
        elif il_abs < 0.10:  # < 10%
            return 'high'
        else:  # >= 10%
            return 'critical'


class NetPnLCalculator:
    """
    Handles Net P&L calculations with gas costs and fees.
    
    Implements the Master Plan formula:
    Net P&L = (Current LP Value + Earned Fees) - (Initial Investment + Gas Costs)
    """
    
    def __init__(self):
        """Initialize the Net P&L calculator."""
        self.logger = logging.getLogger(__name__)
        self.il_calculator = ImpermanentLossCalculator()
    
    def calculate_earned_fees(
        self, 
        initial_investment_usd: float, 
        apr: float, 
        days_held: int
    ) -> float:
        """
        Calculate fees earned from LP position.
        
        Args:
            initial_investment_usd: Initial investment amount in USD
            apr: Annual Percentage Rate (as decimal, e.g., 0.15 for 15%)
            days_held: Number of days position was held
            
        Returns:
            float: Estimated fees earned in USD
        """
        try:
            if initial_investment_usd <= 0 or apr < 0 or days_held < 0:
                return 0.0
            
            # Formula: Investment * (APR / 365) * days_held
            fees_earned = initial_investment_usd * (apr / 365) * days_held
            
            self.logger.debug(
                f"Fees calculation: ${initial_investment_usd:.2f} * "
                f"({apr:.1%} / 365) * {days_held} days = ${fees_earned:.2f}"
            )
            
            return fees_earned
            
        except Exception as e:
            self.logger.error(f"Error calculating earned fees: {e}")
            return 0.0
    
    def calculate_net_pnl(
        self,
        current_lp_value_usd: float,
        earned_fees_usd: float,
        initial_investment_usd: float,
        gas_costs_usd: float
    ) -> Dict[str, float]:
        """
        Calculate Net P&L using the Master Plan formula.
        
        Net P&L = (Current LP Value + Earned Fees) - (Initial Investment + Gas Costs)
        
        Args:
            current_lp_value_usd: Current value of LP position in USD
            earned_fees_usd: Fees earned from LP position
            initial_investment_usd: Initial investment amount
            gas_costs_usd: Gas costs paid for entering position
            
        Returns:
            Dict with detailed P&L breakdown
        """
        try:
            # Calculate total income and costs
            total_income = current_lp_value_usd + earned_fees_usd
            total_costs = initial_investment_usd + gas_costs_usd
            
            # Net P&L calculation
            net_pnl_usd = total_income - total_costs
            net_pnl_percentage = (net_pnl_usd / total_costs) if total_costs > 0 else 0.0
            
            # Break down components
            lp_value_change = current_lp_value_usd - initial_investment_usd
            fees_impact = earned_fees_usd
            gas_impact = -gas_costs_usd  # Negative because it's a cost
            
            result = {
                # Income components
                'current_lp_value_usd': current_lp_value_usd,
                'earned_fees_usd': earned_fees_usd,
                'total_income_usd': total_income,
                
                # Cost components  
                'initial_investment_usd': initial_investment_usd,
                'gas_costs_usd': gas_costs_usd,
                'total_costs_usd': total_costs,
                
                # Net results
                'net_pnl_usd': net_pnl_usd,
                'net_pnl_percentage': net_pnl_percentage,
                
                # Impact breakdown
                'lp_value_change_usd': lp_value_change,
                'fees_impact_usd': fees_impact,
                'gas_impact_usd': gas_impact,
                
                # Status
                'is_profitable': net_pnl_usd > 0,
                'break_even_point': total_costs,
                'calculation_time': datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(
                f"Net P&L calculated: ${net_pnl_usd:.2f} ({net_pnl_percentage:.2%})"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating Net P&L: {e}")
            return {
                'net_pnl_usd': 0.0,
                'net_pnl_percentage': 0.0,
                'is_profitable': False,
                'error': str(e)
            }
    
    def analyze_position_with_fees(
        self,
        position_data: Dict[str, Any],
        current_lp_value_usd: float,
        current_price_a: float,
        current_price_b: float,
        apr: float
    ) -> Dict[str, Any]:
        """
        Complete analysis of LP position including fees and gas costs.
        
        Args:
            position_data: Position configuration from positions.json
            current_lp_value_usd: Current value of LP position
            current_price_a: Current price of token A
            current_price_b: Current price of token B
            apr: Annual Percentage Rate for the pool
            
        Returns:
            Dict with complete position analysis
        """
        try:
            # Extract position data
            initial_liquidity_a = position_data['initial_liquidity_a']
            initial_liquidity_b = position_data['initial_liquidity_b']
            initial_price_a = position_data['initial_price_a_usd']
            initial_price_b = position_data['initial_price_b_usd']
            gas_costs_usd = position_data.get('gas_costs_usd', 0.0)
            
            # Parse real date instead of mock days
            entry_date_str = position_data.get('entry_date')
            if entry_date_str:
                entry_date = datetime.fromisoformat(entry_date_str.replace('Z', '+00:00'))
                current_date = datetime.now(timezone.utc)
                days_held = (current_date - entry_date).days
            else:
                # Fallback to mock data if entry_date not available
                days_held = position_data.get('days_held_mock', 0)
            
            # Calculate initial investment
            initial_investment = (initial_liquidity_a * initial_price_a + 
                                initial_liquidity_b * initial_price_b)
            
            # Calculate earned fees
            earned_fees = self.calculate_earned_fees(initial_investment, apr, days_held)
            
            # Calculate IL
            initial_ratio = initial_price_a / initial_price_b
            current_ratio = current_price_a / current_price_b
            il = self.il_calculator.calculate_impermanent_loss(initial_ratio, current_ratio)
            
            # Calculate Net P&L
            net_pnl_data = self.calculate_net_pnl(
                current_lp_value_usd,
                earned_fees,
                initial_investment,
                gas_costs_usd
            )
            
            # Calculate what would happen if just holding
            hold_value = (initial_liquidity_a * current_price_a + 
                         initial_liquidity_b * current_price_b)
            hold_pnl = hold_value - initial_investment
            
            # Compare strategies (with gas costs)
            lp_total_value = current_lp_value_usd + earned_fees
            lp_vs_hold = lp_total_value - hold_value
            
            result = {
                'position_info': {
                    'name': position_data.get('name', 'Unknown'),
                    'initial_investment_usd': initial_investment,
                    'days_held': days_held,
                    'gas_costs_usd': gas_costs_usd
                },
                'current_status': {
                    'current_lp_value_usd': current_lp_value_usd,
                    'earned_fees_usd': earned_fees,
                    'total_lp_value_usd': lp_total_value,
                    'il_percentage': il,
                    'il_usd': hold_value - current_lp_value_usd
                },
                'net_pnl': net_pnl_data,
                'strategy_comparison': {
                    'hold_value_usd': hold_value,
                    'hold_pnl_usd': hold_pnl,
                    'lp_advantage_usd': lp_vs_hold,
                    'better_strategy': 'LP' if lp_vs_hold > 0 else 'Hold'
                },
                'fees_analysis': {
                    'apr_used': apr,
                    'daily_fee_rate': apr / 365,
                    'fees_offset_il': earned_fees > abs(hold_value - current_lp_value_usd)
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in position analysis: {e}")
            return {'error': str(e)}


# Risk assessment utility functions
class RiskAssessment:
    """
    Additional risk assessment utilities.
    """
    
    @staticmethod
    def get_risk_category(token_a_symbol: str, token_b_symbol: str) -> str:
        """
        Categorize risk level based on token pair.
        
        Args:
            token_a_symbol: Symbol of token A
            token_b_symbol: Symbol of token B
            
        Returns:
            str: Risk category
        """
        stablecoins = {'USDC', 'USDT', 'DAI', 'BUSD', 'FRAX'}
        major_tokens = {'ETH', 'WETH', 'BTC', 'WBTC'}
        
        tokens = {token_a_symbol.upper(), token_b_symbol.upper()}
        
        if len(tokens.intersection(stablecoins)) == 2:
            return 'very_low'
        elif len(tokens.intersection(stablecoins)) == 1:
            return 'low'
        elif len(tokens.intersection(major_tokens)) >= 1:
            return 'medium'
        else:
            return 'high'
    
    @staticmethod
    def get_recommended_il_threshold(risk_category: str) -> float:
        """
        Get recommended IL threshold based on risk category.
        
        Args:
            risk_category: Risk category
            
        Returns:
            float: Recommended threshold
        """
        thresholds = {
            'very_low': 0.005,  # 0.5%
            'low': 0.02,        # 2%
            'medium': 0.05,     # 5%
            'high': 0.10        # 10%
        }
        
        return thresholds.get(risk_category, 0.05)