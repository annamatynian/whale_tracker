"""
Token Contract Address Mapping

Maps token symbols to their Ethereum contract addresses.
Used for DefiLlama API queries and other on-chain data providers.

Format: ethereum:{contract_address}
"""

from typing import Dict


# Token contract addresses on Ethereum Mainnet
TOKEN_CONTRACTS: Dict[str, str] = {
    # Native ETH (special case - zero address)
    'ETH': '0x0000000000000000000000000000000000000000',

    # Stablecoins
    'USDT': '0xdac17f958d2ee523a2206206994597c13d831ec7',  # Tether USD
    'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',  # USD Coin
    'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f',   # Dai Stablecoin
    'BUSD': '0x4fabb145d64652a948d72533023f6e7a623c7c53',  # Binance USD

    # Wrapped tokens
    'WETH': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',  # Wrapped Ether
    'WBTC': '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',  # Wrapped Bitcoin

    # DeFi tokens
    'UNI': '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984',   # Uniswap
    'AAVE': '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9',  # Aave
    'LINK': '0x514910771af9ca656af840dff83e8264ecf986ca',  # Chainlink
    'SNX': '0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f',   # Synthetix
    'MKR': '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2',   # Maker
    'COMP': '0xc00e94cb662c3520282e6f5717214004a7f26888',  # Compound

    # Popular altcoins
    'SHIB': '0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce',  # Shiba Inu
    'PEPE': '0x6982508145454ce325ddbe47a25d4ec3d2311933',  # Pepe
    'APE': '0x4d224452801aced8b2f0aebe155379bb5d594381',   # ApeCoin
    'LDO': '0x5a98fcbea516cf06857215779fd812ca3bef1b32',   # Lido DAO

    # Layer 2 tokens
    'MATIC': '0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0',  # Polygon
    'ARB': '0xb50721bcf8d664c30412cfbc6cf7a15145f1de8',    # Arbitrum (placeholder)
    'OP': '0x4200000000000000000000000000000000000042',    # Optimism
}


def get_defillama_id(symbol: str) -> str:
    """
    Get DefiLlama token ID for a given symbol.

    DefiLlama uses format: chain:contract_address
    For Ethereum: ethereum:0x...

    Args:
        symbol: Token symbol (ETH, USDT, etc.)

    Returns:
        str: DefiLlama token ID (ethereum:0x...)

    Raises:
        ValueError: If token symbol is not found

    Example:
        >>> get_defillama_id('ETH')
        'ethereum:0x0000000000000000000000000000000000000000'
        >>> get_defillama_id('USDT')
        'ethereum:0xdac17f958d2ee523a2206206994597c13d831ec7'
    """
    symbol_upper = symbol.upper()

    if symbol_upper not in TOKEN_CONTRACTS:
        raise ValueError(
            f"Unknown token symbol: {symbol}. "
            f"Available tokens: {', '.join(TOKEN_CONTRACTS.keys())}"
        )

    contract_address = TOKEN_CONTRACTS[symbol_upper]
    return f"ethereum:{contract_address}"


def get_contract_address(symbol: str) -> str:
    """
    Get Ethereum contract address for a given symbol.

    Args:
        symbol: Token symbol (ETH, USDT, etc.)

    Returns:
        str: Contract address (0x...)

    Raises:
        ValueError: If token symbol is not found

    Example:
        >>> get_contract_address('USDT')
        '0xdac17f958d2ee523a2206206994597c13d831ec7'
    """
    symbol_upper = symbol.upper()

    if symbol_upper not in TOKEN_CONTRACTS:
        raise ValueError(
            f"Unknown token symbol: {symbol}. "
            f"Available tokens: {', '.join(TOKEN_CONTRACTS.keys())}"
        )

    return TOKEN_CONTRACTS[symbol_upper]


def is_supported(symbol: str) -> bool:
    """
    Check if token symbol is supported.

    Args:
        symbol: Token symbol to check

    Returns:
        bool: True if symbol is supported

    Example:
        >>> is_supported('ETH')
        True
        >>> is_supported('UNKNOWN')
        False
    """
    return symbol.upper() in TOKEN_CONTRACTS


def get_supported_tokens() -> list[str]:
    """
    Get list of all supported token symbols.

    Returns:
        list[str]: List of supported symbols

    Example:
        >>> tokens = get_supported_tokens()
        >>> 'ETH' in tokens
        True
    """
    return list(TOKEN_CONTRACTS.keys())


# Add more tokens as needed
# To add a new token:
# 1. Find contract address on Etherscan
# 2. Add to TOKEN_CONTRACTS dict above
# 3. Token will be automatically available in DefiLlama queries
