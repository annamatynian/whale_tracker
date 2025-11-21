"""
Abstract Base Classes for Whale Tracker

This package contains all abstract interfaces that enable
pluggable, testable, and maintainable architecture.
"""

from src.abstractions.notification_provider import NotificationProvider
from src.abstractions.rpc_provider import RPCProvider
from src.abstractions.cooldown_storage import CooldownStorage
from src.abstractions.blockchain_data_provider import BlockchainDataProvider
from src.abstractions.detection_repository import DetectionRepository
from src.abstractions.price_provider import PriceProvider

__all__ = [
    'NotificationProvider',
    'RPCProvider',
    'CooldownStorage',
    'BlockchainDataProvider',
    'DetectionRepository',
    'PriceProvider',
]
