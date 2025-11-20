"""
OnChain Agent - Deep blockchain analysis for token safety assessment
Performs quantitative analysis of liquidity locks and holder concentration
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from tools.blockchain.rpc_manager import RPCManager
from tools.blockchain.etherscan_client import EtherscanClient, TokenHolder


@dataclass
class LiquidityAnalysis:
    """Result of LP token analysis."""
    total_lp_supply: int
    locked_percentage: float
    dead_percentage: float
    unknown_contract_percentage: float
    eoa_controlled_percentage: float
    risk_level: str  # "SAFE", "MODERATE", "HIGH", "CRITICAL"
    details: List[str]


@dataclass
class HolderAnalysis:
    """Result of token holder concentration analysis."""
    total_holders: int
    top_10_concentration: float
    top_20_concentration: float
    exchange_percentage: float
    contract_percentage: float
    risk_level: str  # "LOW", "MODERATE", "HIGH", "CRITICAL"
    details: List[str]


@dataclass
class OnChainAnalysisResult:
    """Complete onchain analysis result."""
    lp_analysis: Optional[LiquidityAnalysis]
    holder_analysis: Optional[HolderAnalysis]
    overall_risk: str  # "SAFE", "MODERATE", "HIGH", "CRITICAL"
    recommendation: str
    analysis_errors: List[str]
    api_calls_used: int = 0  # Track RPC calls used


class OnChainAgent:
    """Performs deep onchain analysis for token safety assessment."""

    def __init__(self, mock_mode: bool = False):
        """
        Initialize OnChain Agent.
        
        Args:
            mock_mode: If True, use mock data instead of real API calls
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mock_mode = mock_mode
        
        # Initialize components
        self.rpc_manager = RPCManager(mock_mode=mock_mode)
        self.etherscan_client = EtherscanClient(mock_mode=mock_mode)
        
        # Load known locker configurations
        self.known_lockers = self._load_known_lockers()
        
        # Configuration from environment
        self.config = {
            "lp_safe_threshold": float(os.getenv("ONCHAIN_LP_SAFE_THRESHOLD", "80")),
            "concentration_limit": float(os.getenv("ONCHAIN_HOLDER_CONCENTRATION_LIMIT", "40")),
            "min_score_threshold": float(os.getenv("ONCHAIN_MIN_SCORE_THRESHOLD", "70"))
        }
        
        if not mock_mode:
            self.logger.info("OnChain Agent инициализирован для реального анализа")
        else:
            self.logger.info("OnChain Agent инициализирован в MOCK режиме")

    def _load_known_lockers(self) -> Dict:
        """Load known locker contracts configuration."""
        config_path = Path(__file__).parent.parent.parent / "config" / "known_lockers.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации локкеров: {e}")
            return {}

    def _is_known_locker(self, network: str, address: str) -> bool:
        """Check if address is a known liquidity locker."""
        network_config = self.known_lockers.get(network, {})
        
        for service_name, service_config in network_config.items():
            if service_name in ["dead_addresses", "trust_levels", "notes"]:
                continue
                
            contracts = service_config.get("contracts", [])
            if address.lower() in [contract.lower() for contract in contracts]:
                return True
        
        return False

    def _is_dead_address(self, address: str) -> bool:
        """Check if address is a known dead/burn address."""
        dead_addresses = self.known_lockers.get("dead_addresses", {}).get("addresses", [])
        return address.lower() in [addr.lower() for addr in dead_addresses]

    async def analyze_lp_tokens(self, network: str, lp_token_address: str) -> LiquidityAnalysis:
        """
        Analyze LP token distribution for rug pull risk assessment.
        
        Args:
            network: Network name (ethereum, base, etc.)
            lp_token_address: LP token contract address
            
        Returns:
            LiquidityAnalysis result
        """
        details = []
        
        try:
            # Get total LP supply
            total_supply = self.rpc_manager.get_token_total_supply(network, lp_token_address)
            details.append(f"Total LP supply: {total_supply}")
            
            # Get top LP holders
            lp_holders = await self.etherscan_client.get_token_holders(
                network, lp_token_address, limit=50
            )
            
            if not lp_holders:
                return LiquidityAnalysis(
                    total_lp_supply=total_supply,
                    locked_percentage=0.0,
                    dead_percentage=0.0,
                    unknown_contract_percentage=0.0,
                    eoa_controlled_percentage=100.0,
                    risk_level="CRITICAL",
                    details=["Не удалось получить список держателей LP"]
                )
            
            # Analyze holder types
            locked_percentage = 0.0
            dead_percentage = 0.0
            unknown_contract_percentage = 0.0
            eoa_controlled_percentage = 0.0
            
            for holder in lp_holders:
                percentage = holder.percentage
                
                if self._is_dead_address(holder.address):
                    dead_percentage += percentage
                    details.append(f"Dead address {holder.address[:10]}...: {percentage:.2f}%")
                    
                elif self._is_known_locker(network, holder.address):
                    locked_percentage += percentage
                    details.append(f"Known locker {holder.address[:10]}...: {percentage:.2f}%")
                    
                else:
                    # Check if it's a contract
                    is_contract = self.rpc_manager.is_contract(network, holder.address)
                    
                    if is_contract:
                        unknown_contract_percentage += percentage
                        details.append(f"Unknown contract {holder.address[:10]}...: {percentage:.2f}%")
                    else:
                        eoa_controlled_percentage += percentage
                        details.append(f"EOA wallet {holder.address[:10]}...: {percentage:.2f}%")
            
            # Calculate total safe percentage
            safe_percentage = locked_percentage + dead_percentage
            
            # Determine risk level
            if safe_percentage >= self.config["lp_safe_threshold"]:
                risk_level = "SAFE"
            elif safe_percentage >= 50:
                risk_level = "MODERATE"  
            elif eoa_controlled_percentage > 50:
                risk_level = "CRITICAL"
            else:
                risk_level = "HIGH"
            
            details.append(f"Total safe percentage: {safe_percentage:.2f}%")
            details.append(f"Risk assessment: {risk_level}")
            
            return LiquidityAnalysis(
                total_lp_supply=total_supply,
                locked_percentage=locked_percentage,
                dead_percentage=dead_percentage,
                unknown_contract_percentage=unknown_contract_percentage,
                eoa_controlled_percentage=eoa_controlled_percentage,
                risk_level=risk_level,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа LP токенов: {e}")
            return LiquidityAnalysis(
                total_lp_supply=0,
                locked_percentage=0.0,
                dead_percentage=0.0,
                unknown_contract_percentage=0.0,
                eoa_controlled_percentage=100.0,
                risk_level="CRITICAL",
                details=[f"Ошибка анализа: {str(e)}"]
            )

    async def analyze_holder_concentration(self, network: str, token_address: str) -> HolderAnalysis:
        """
        Analyze token holder concentration for dump risk assessment.
        
        Args:
            network: Network name
            token_address: Main token contract address
            
        Returns:
            HolderAnalysis result
        """
        details = []
        
        try:
            # Get top token holders
            holders = await self.etherscan_client.get_token_holders(
                network, token_address, limit=50
            )
            
            if not holders:
                return HolderAnalysis(
                    total_holders=0,
                    top_10_concentration=100.0,
                    top_20_concentration=100.0,
                    exchange_percentage=0.0,
                    contract_percentage=0.0,
                    risk_level="CRITICAL",
                    details=["Не удалось получить список держателей токена"]
                )
            
            # Filter out known exchanges and contracts
            filtered_holders = []
            exchange_percentage = 0.0
            contract_percentage = 0.0
            
            for holder in holders:
                holder_type = self.etherscan_client.classify_holder_type(holder)
                
                if holder_type == "LIKELY_EXCHANGE":
                    exchange_percentage += holder.percentage
                    details.append(f"Exchange {holder.address[:10]}...: {holder.percentage:.2f}%")
                    
                elif holder_type in ["UNKNOWN_CONTRACT", "DEAD_ADDRESS"]:
                    contract_percentage += holder.percentage
                    details.append(f"Contract {holder.address[:10]}...: {holder.percentage:.2f}%")
                    
                else:  # EOA wallets
                    filtered_holders.append(holder)
            
            # Calculate concentration among anonymous EOA wallets
            top_10_concentration = sum(h.percentage for h in filtered_holders[:10])
            top_20_concentration = sum(h.percentage for h in filtered_holders[:20])
            
            # Determine risk level
            if top_10_concentration > self.config["concentration_limit"]:
                risk_level = "HIGH"
            elif top_10_concentration > 25:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"
            
            details.append(f"Top 10 EOA concentration: {top_10_concentration:.2f}%")
            details.append(f"Top 20 EOA concentration: {top_20_concentration:.2f}%")
            details.append(f"Risk assessment: {risk_level}")
            
            return HolderAnalysis(
                total_holders=len(holders),
                top_10_concentration=top_10_concentration,
                top_20_concentration=top_20_concentration,
                exchange_percentage=exchange_percentage,
                contract_percentage=contract_percentage,
                risk_level=risk_level,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа концентрации держателей: {e}")
            return HolderAnalysis(
                total_holders=0,
                top_10_concentration=100.0,
                top_20_concentration=100.0,
                exchange_percentage=0.0,
                contract_percentage=0.0,
                risk_level="CRITICAL",
                details=[f"Ошибка анализа: {str(e)}"]
            )

    async def analyze_token(self, network: str, token_address: str, 
                          lp_address: Optional[str] = None) -> OnChainAnalysisResult:
        """
        Perform complete onchain analysis for a token.
        
        Args:
            network: Network name
            token_address: Main token contract address
            lp_address: LP token address (optional)
            
        Returns:
            Complete OnChainAnalysisResult
        """
        analysis_errors = []
        lp_analysis = None
        holder_analysis = None
        total_api_calls = 0
        
        if self.mock_mode:
            # В mock режиме возвращаем заглушку без API calls
            self.logger.debug(f"MOCK: Анализ {token_address} (mock режим)")
            return OnChainAnalysisResult(
                lp_analysis=None,
                holder_analysis=None,
                overall_risk="MODERATE",
                recommendation="MOCK_ANALYSIS",
                analysis_errors=["Mock mode - no real analysis"],
                api_calls_used=0
            )
        
        # Analyze LP tokens if address provided
        if lp_address:
            try:
                self.logger.debug(f"Анализ LP токенов для {lp_address}")
                lp_analysis = await self.analyze_lp_tokens(network, lp_address)
                total_api_calls += 1  # RPC call for total supply
                total_api_calls += 1  # Etherscan call for holders
                
                # Count contract checks (1 RPC call per holder)
                if hasattr(lp_analysis, 'details'):
                    contract_checks = len([d for d in lp_analysis.details if 'contract' in d.lower()])
                    total_api_calls += contract_checks
                    
            except Exception as e:
                analysis_errors.append(f"LP analysis failed: {str(e)}")
        
        # Analyze holder concentration
        try:
            self.logger.debug(f"Анализ концентрации держателей для {token_address}")
            holder_analysis = await self.analyze_holder_concentration(network, token_address)
            total_api_calls += 1  # Etherscan call for token holders
            
        except Exception as e:
            analysis_errors.append(f"Holder analysis failed: {str(e)}")
        
        # Determine overall risk
        overall_risk = "MODERATE"
        recommendation = "PROCEED_WITH_CAUTION"
        
        if lp_analysis and lp_analysis.risk_level == "CRITICAL":
            overall_risk = "CRITICAL"
            recommendation = "AVOID_HIGH_RUG_RISK"
        elif holder_analysis and holder_analysis.risk_level == "HIGH":
            overall_risk = "HIGH"
            recommendation = "PROCEED_WITH_CAUTION"
        elif (lp_analysis and lp_analysis.risk_level == "SAFE" and 
              holder_analysis and holder_analysis.risk_level == "LOW"):
            overall_risk = "SAFE"
            recommendation = "SAFE_TO_PROCEED"
        
        self.logger.info(f"OnChain анализ завершен для {token_address}: {total_api_calls} API calls, риск: {overall_risk}")
        
        return OnChainAnalysisResult(
            lp_analysis=lp_analysis,
            holder_analysis=holder_analysis,
            overall_risk=overall_risk,
            recommendation=recommendation,
            analysis_errors=analysis_errors,
            api_calls_used=total_api_calls
        )

    def get_analysis_summary(self, result: OnChainAnalysisResult) -> Dict:
        """Generate summary for integration with scoring system."""
        summary = {
            "overall_risk": result.overall_risk,
            "recommendation": result.recommendation,
            "lp_safety_score": 0,
            "holder_safety_score": 0,
            "onchain_bonus": 0
        }
        
        # Calculate LP safety score (0-10)
        if result.lp_analysis:
            safe_percentage = (result.lp_analysis.locked_percentage + 
                             result.lp_analysis.dead_percentage)
            
            if safe_percentage >= 90:
                summary["lp_safety_score"] = 10
            elif safe_percentage >= 80:
                summary["lp_safety_score"] = 8
            elif safe_percentage >= 50:
                summary["lp_safety_score"] = 5
            else:
                summary["lp_safety_score"] = 0
        
        # Calculate holder safety score (0-5)
        if result.holder_analysis:
            concentration = result.holder_analysis.top_10_concentration
            
            if concentration < 20:
                summary["holder_safety_score"] = 5
            elif concentration < 30:
                summary["holder_safety_score"] = 3
            elif concentration < 40:
                summary["holder_safety_score"] = 1
            else:
                summary["holder_safety_score"] = 0
        
        # Calculate overall onchain bonus (0-15)
        summary["onchain_bonus"] = (summary["lp_safety_score"] + 
                                  summary["holder_safety_score"])
        
        return summary
