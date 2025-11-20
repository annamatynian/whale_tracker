"""
Position Manager - Data Persistence and Position Management
=========================================================

This module handles:
- Loading/saving position data with Pydantic validation
- Position configuration management
- Historical data tracking
- Backup and recovery

Author: Generated for DeFi-RAG Project
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from decimal import Decimal

# Import our Pydantic models
from .position_models import (
    LPPosition, 
    HistoricalDataEntry, 
    PositionAnalysis,
    TokenInfo,
    SupportedNetwork,
    SupportedProtocol,
    create_example_position_model,
    validate_position_dict
)


class PositionManager:
    """
    Manages LP position data and persistence.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize Position Manager.
        
        Args:
            data_dir: Directory for data files
        """
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(data_dir)
        self.positions_file = self.data_dir / "positions.json"
        self.history_file = self.data_dir / "position_history.json"
        self.backup_dir = self.data_dir / "backups"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all necessary directories exist."""
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
    
    def load_positions(self) -> List[LPPosition]:
        """
        Load all positions from storage.
        
        Returns:
            List[LPPosition]: List of validated position models
        """
        try:
            if not self.positions_file.exists():
                self.logger.info("No positions file found, starting with empty list")
                return []
            
            with open(self.positions_file, 'r') as f:
                positions_data = json.load(f)
            
            # Convert dictionaries to Pydantic models
            positions = []
            for pos_data in positions_data:
                try:
                    # Use Pydantic model_validate method
                    position = LPPosition.model_validate(pos_data)
                    positions.append(position)
                except Exception as e:
                    self.logger.error(f"Error loading position '{pos_data.get('name', 'unknown')}': {e}")
                    # Skip invalid positions
                    continue
            
            self.logger.info(f"Loaded {len(positions)} valid positions from storage")
            return positions
            
        except Exception as e:
            self.logger.error(f"Error loading positions: {e}")
            return []
    
    def save_positions(self, positions: List[LPPosition]) -> bool:
        """
        Save positions to storage.
        
        Args:
            positions: List of validated LPPosition models
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Create backup first
            self._create_backup()
            
            # Convert models to dictionaries for JSON serialization
            positions_data = [pos.to_dict() for pos in positions]
            
            # Save current positions
            with open(self.positions_file, 'w') as f:
                json.dump(positions_data, f, indent=2, default=str)
            
            self.logger.debug(f"Saved {len(positions)} positions to storage")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving positions: {e}")
            return False
    
    def add_position(self, position_config: Union[Dict[str, Any], LPPosition]) -> bool:
        """
        Add a new position to tracking with validation.
        
        Args:
            position_config: Position configuration (dict or LPPosition model)
            
        Returns:
            bool: True if added successfully
        """
        try:
            # Convert to LPPosition model if it's a dictionary
            if isinstance(position_config, dict):
                # Validate first
                validation_errors = validate_position_dict(position_config)
                if validation_errors:
                    for error in validation_errors:
                        self.logger.error(f"Position validation error: {error}")
                    return False
                
                position = LPPosition.from_dict(position_config)
            elif isinstance(position_config, LPPosition):
                position = position_config
            else:
                self.logger.error("Position config must be dict or LPPosition model")
                return False
            
            # Load existing positions
            positions = self.load_positions()
            
            # Check if position already exists
            existing = any(p.name == position.name for p in positions)
            
            if existing:
                self.logger.warning(f"Position {position.name} already exists")
                return False
            
            # Add position
            positions.append(position)
            
            # Save
            if self.save_positions(positions):
                self.logger.info(f"Added new position: {position.name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error adding position: {e}")
            return False
    
    def update_position(self, position_name: str, updates: Dict[str, Any]) -> bool:
        """
        Update existing position.
        
        Args:
            position_name: Name of position to update
            updates: Update data
            
        Returns:
            bool: True if updated successfully
        """
        try:
            positions = self.load_positions()
            
            # Find position
            position_index = None
            for i, position in enumerate(positions):
                if position.name == position_name:
                    position_index = i
                    break
            
            if position_index is None:
                self.logger.warning(f"Position {position_name} not found for update")
                return False
            
            # Get current position and convert to dict for updating
            current_position = positions[position_index]
            position_dict = current_position.to_dict()
            
            # Apply updates
            position_dict.update(updates)
            position_dict['last_updated'] = datetime.now().isoformat()
            
            # Create new position model from updated dict
            updated_position = LPPosition.from_dict(position_dict)
            positions[position_index] = updated_position
            
            # Save
            if self.save_positions(positions):
                self.logger.debug(f"Updated position: {position_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
            return False
    
    def remove_position(self, position_name: str) -> bool:
        """
        Remove position from tracking.
        
        Args:
            position_name: Name of position to remove
            
        Returns:
            bool: True if removed successfully
        """
        try:
            positions = self.load_positions()
            
            # Filter out the position
            original_count = len(positions)
            positions = [p for p in positions if p.name != position_name]
            
            if len(positions) == original_count:
                self.logger.warning(f"Position {position_name} not found for removal")
                return False
            
            # Save
            if self.save_positions(positions):
                self.logger.info(f"Removed position: {position_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing position: {e}")
            return False
    
    def get_position(self, position_name: str) -> Optional[LPPosition]:
        """
        Get specific position by name.
        
        Args:
            position_name: Position name
            
        Returns:
            Optional[LPPosition]: Position model or None
        """
        try:
            positions = self.load_positions()
            
            for position in positions:
                if position.name == position_name:
                    return position
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting position: {e}")
            return None
    
    def save_historical_data(
        self, 
        position_name: str, 
        analysis_data: Union[Dict[str, Any], PositionAnalysis]
    ) -> bool:
        """
        Save historical analysis data for trending.
        
        Args:
            position_name: Position name
            analysis_data: Analysis results (dict or PositionAnalysis model)
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Load existing history
            history = self._load_history()
            
            # Create historical entry
            if isinstance(analysis_data, PositionAnalysis):
                # Convert PositionAnalysis to HistoricalDataEntry
                entry = HistoricalDataEntry(
                    position_name=position_name,
                    current_il_percentage=analysis_data.il_percentage,
                    current_value_usd=analysis_data.current_position_value_usd,
                    hold_value_usd=analysis_data.hold_strategy_value_usd,
                    fees_earned_usd=analysis_data.total_fees_earned_usd,
                    token_a_price_usd=analysis_data.token_a_price_current,
                    token_b_price_usd=analysis_data.token_b_price_current,
                    price_ratio=analysis_data.current_price_ratio
                )
            else:
                # Create from dictionary
                entry = HistoricalDataEntry(
                    position_name=position_name,
                    current_il_percentage=analysis_data.get('il_percentage'),
                    current_value_usd=analysis_data.get('current_value_usd'),
                    hold_value_usd=analysis_data.get('hold_value_usd'),
                    fees_earned_usd=analysis_data.get('fees_earned_usd'),
                    token_a_price_usd=analysis_data.get('token_a_price_usd'),
                    token_b_price_usd=analysis_data.get('token_b_price_usd'),
                    price_ratio=analysis_data.get('price_ratio')
                )
            
            # Add to history
            history.append(entry.to_dict())
            
            # Keep only last 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            history = [
                h for h in history 
                if datetime.fromisoformat(h['timestamp']) > cutoff_date
            ]
            
            # Save history
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
            
            self.logger.debug(f"Saved historical data for {position_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving historical data: {e}")
            return False
    
    def get_historical_data(
        self, 
        position_name: str, 
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get historical data for position.
        
        Args:
            position_name: Position name
            days: Number of days to retrieve
            
        Returns:
            List[Dict]: Historical data points
        """
        try:
            history = self._load_history()
            
            # Filter by position and date
            cutoff_date = datetime.now() - timedelta(days=days)
            
            filtered_history = [
                h for h in history
                if (h.get('position_name') == position_name and 
                    datetime.fromisoformat(h['timestamp']) > cutoff_date)
            ]
            
            # Sort by timestamp
            filtered_history.sort(key=lambda x: x['timestamp'])
            
            return filtered_history
            
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return []
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load historical data from file."""
        try:
            if not self.history_file.exists():
                return []
            
            with open(self.history_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")
            return []
    
    def _create_backup(self) -> bool:
        """Create backup of current positions file."""
        try:
            if not self.positions_file.exists():
                return True
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"positions_backup_{timestamp}.json"
            
            # Copy current file to backup
            with open(self.positions_file, 'r') as src:
                with open(backup_file, 'w') as dst:
                    dst.write(src.read())
            
            # Clean old backups (keep only last 10)
            self._cleanup_old_backups()
            
            self.logger.debug(f"Created backup: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Clean up old backup files."""
        try:
            backup_files = list(self.backup_dir.glob("positions_backup_*.json"))
            
            if len(backup_files) <= keep_count:
                return
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old files
            for old_file in backup_files[keep_count:]:
                old_file.unlink()
                self.logger.debug(f"Removed old backup: {old_file}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {e}")
    
    def export_data(self, export_path: str) -> bool:
        """
        Export all data to a file.
        
        Args:
            export_path: Path for export file
            
        Returns:
            bool: True if exported successfully
        """
        try:
            positions = self.load_positions()
            history = self._load_history()
            
            # Convert positions to dictionaries for JSON serialization
            positions_data = [pos.to_dict() for pos in positions]
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'positions': positions_data,
                'history': history
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported data to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return False
    
    def import_data(self, import_path: str) -> bool:
        """
        Import data from a file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            bool: True if imported successfully
        """
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            # Validate structure
            if 'positions' not in import_data:
                self.logger.error("Invalid import file: no positions data")
                return False
            
            # Create backup before import
            self._create_backup()
            
            # Import positions - convert dictionaries to LPPosition models
            positions_data = import_data['positions']
            positions = []
            
            for pos_data in positions_data:
                try:
                    position = LPPosition.from_dict(pos_data)
                    positions.append(position)
                except Exception as e:
                    self.logger.error(f"Error importing position '{pos_data.get('name', 'unknown')}': {e}")
                    continue
            
            if self.save_positions(positions):
                self.logger.info(f"Imported {len(positions)} valid positions from {len(positions_data)} total")
                
                # Import history if available
                if 'history' in import_data:
                    with open(self.history_file, 'w') as f:
                        json.dump(import_data['history'], f, indent=2, default=str)
                    self.logger.info("Imported historical data")
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error importing data: {e}")
            return False


def create_example_position() -> LPPosition:
    """
    Create an example position configuration using Pydantic model.
    
    Returns:
        LPPosition: Example position model
    """
    return create_example_position_model()


def create_example_position_dict() -> Dict[str, Any]:
    """
    Create an example position configuration as dictionary (legacy compatibility).
    
    Returns:
        Dict: Example position dictionary
    """
    position = create_example_position_model()
    return position.to_dict()


# Enhanced Position Validator using Pydantic
class PositionValidator:
    """
    Enhanced position validator using Pydantic models.
    """
    
    @staticmethod
    def validate_position(position: Union[Dict[str, Any], LPPosition]) -> List[str]:
        """
        Validate position configuration using Pydantic.
        
        Args:
            position: Position data (dict or LPPosition model)
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        try:
            if isinstance(position, LPPosition):
                return []  # Already validated by Pydantic
            
            return validate_position_dict(position)
            
        except Exception as e:
            return [str(e)]
    
    @staticmethod
    def is_valid_position(position: Union[Dict[str, Any], LPPosition]) -> bool:
        """
        Check if position is valid.
        
        Args:
            position: Position data (dict or LPPosition model)
            
        Returns:
            bool: True if valid
        """
        return len(PositionValidator.validate_position(position)) == 0
    
    @staticmethod
    def validate_ethereum_address(address: str) -> bool:
        """
        Validate Ethereum address format.
        
        Args:
            address: Address string
            
        Returns:
            bool: True if valid
        """
        try:
            TokenInfo(symbol="TEST", address=address)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_position_risk_level(position: LPPosition) -> str:
        """
        Determine risk level based on position configuration.
        
        Args:
            position: LP position model
            
        Returns:
            str: Risk level (very_low, low, medium, high)
        """
        # Simple risk assessment based on token types
        token_a_symbol = position.token_a.symbol.upper()
        token_b_symbol = position.token_b.symbol.upper()
        
        stablecoins = {'USDC', 'USDT', 'DAI', 'BUSD', 'FRAX'}
        major_tokens = {'ETH', 'WETH', 'BTC', 'WBTC'}
        
        if token_a_symbol in stablecoins and token_b_symbol in stablecoins:
            return 'very_low'
        elif (token_a_symbol in stablecoins and token_b_symbol in major_tokens) or \
             (token_a_symbol in major_tokens and token_b_symbol in stablecoins):
            return 'low'
        elif token_a_symbol in major_tokens and token_b_symbol in major_tokens:
            return 'medium'
        else:
            return 'high'


# Utility function for backward compatibility
def create_example_position() -> LPPosition:
    """
    Create an example position as Pydantic model.
    
    Returns:
        LPPosition: Example position model
    """
    # Return the Pydantic model directly
    return create_example_position_model()
