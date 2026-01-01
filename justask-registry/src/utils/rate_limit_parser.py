#!/usr/bin/env python3
"""
Rate Limit Parser
Parses various rate limit text formats from working_version.rate_limits column
Supports 3 primary formats covering 100% of text-generation models

Ported from: justask-router/selector-service/src/utils/rateLimitParser.js
"""

import re
from typing import Dict, Optional


def parse_token_value(value_str: str) -> Optional[int]:
    """
    Parse token value with K/M suffixes

    Examples:
        "15K" → 15000
        "1M" → 1000000
        "500" → 500

    Args:
        value_str: String containing numeric value with optional K/M suffix

    Returns:
        Parsed integer value or None if parsing fails
    """
    if not value_str:
        return None

    # Match number with optional K/M suffix
    match = re.match(r'([\d.]+)([KkMm]?)', str(value_str))
    if not match:
        return None

    value = float(match.group(1))
    suffix = match.group(2).upper() if match.group(2) else ''

    if suffix == 'K':
        return round(value * 1000)
    elif suffix == 'M':
        return round(value * 1000000)
    else:
        return round(value)


def apply_provider_fallback(result: Dict, provider: str) -> Dict:
    """
    Apply provider-based fallback values when parsing fails

    Args:
        result: Dictionary containing parsed rate limits
        provider: Provider name (groq, google, openrouter)

    Returns:
        Updated result dictionary with fallback values
    """
    fallbacks = {
        'groq': {'rpm': 30, 'rpd': None, 'tpm': 15000, 'tpd': None},
        'google': {'rpm': 15, 'rpd': None, 'tpm': None, 'tpd': None},
        'openrouter': {'rpm': 20, 'rpd': 50, 'tpm': None, 'tpd': None}
    }

    provider_lower = provider.lower() if provider else ''
    fallback = None

    if 'groq' in provider_lower:
        fallback = fallbacks['groq']
    elif 'google' in provider_lower or 'gemini' in provider_lower:
        fallback = fallbacks['google']
    elif 'openrouter' in provider_lower:
        fallback = fallbacks['openrouter']

    if fallback:
        result['rpm'] = fallback['rpm']
        result['rpd'] = fallback['rpd']
        result['tpm'] = fallback['tpm']
        result['tpd'] = fallback['tpd']
        result['parseable'] = False

    return result


def parse_rate_limits(rate_limits_str: str, provider: str) -> Dict:
    """
    Parse rate limits from various text formats

    Format 1 (Google/Gemini): "15 requests/min, 1M tokens/min, 200 requests/day"
    Format 2 (OpenRouter): "20 requests/min 50/day"
    Format 3 (Groq): "RPM: 30, TPM: 15K, RPD: 14.4K, TPD: 500K"

    Args:
        rate_limits_str: Raw rate_limits string from working_version
        provider: inference_provider for fallback

    Returns:
        Dictionary with keys: rpm, rpd, tpm, tpd, parseable
    """
    result = {
        'rpm': None,
        'rpd': None,
        'tpm': None,
        'tpd': None,
        'parseable': True
    }

    # Handle null/empty strings
    if not rate_limits_str or not rate_limits_str.strip():
        return apply_provider_fallback(result, provider)

    lower = rate_limits_str.lower()

    # Format 1: "15 requests/min, 1M tokens/min, 200 requests/day"
    # Characteristics: Contains "requests/min" and comma separator
    if 'requests/min' in lower and ',' in lower:
        rpm_match = re.search(r'(\d+)\s*requests/min', rate_limits_str, re.IGNORECASE)
        tpm_match = re.search(r'([\d.]+[KkMm]?)\s*tokens/min', rate_limits_str, re.IGNORECASE)
        rpd_match = re.search(r'([\d,]+)\s*requests/day', rate_limits_str, re.IGNORECASE)

        if rpm_match:
            result['rpm'] = int(rpm_match.group(1))
        if tpm_match:
            result['tpm'] = parse_token_value(tpm_match.group(1))
        if rpd_match:
            result['rpd'] = int(rpd_match.group(1).replace(',', ''))

        # If we got at least RPM, consider it parsed
        if result['rpm'] is not None:
            return result

    # Format 2: "20 requests/min 50/day"
    # Characteristics: Contains "requests/min" and "/day" but no comma
    elif 'requests/min' in lower and '/day' in lower:
        rpm_match = re.search(r'(\d+)\s*requests/min', rate_limits_str, re.IGNORECASE)
        rpd_match = re.search(r'(\d+)/day', rate_limits_str, re.IGNORECASE)

        if rpm_match:
            result['rpm'] = int(rpm_match.group(1))
        if rpd_match:
            result['rpd'] = int(rpd_match.group(1))

        if result['rpm'] is not None:
            return result

    # Format 3: "RPM: 30, TPM: 15K, RPD: 14.4K, TPD: 500K"
    # Characteristics: Contains "RPM:" prefix
    elif 'rpm:' in lower:
        rpm_match = re.search(r'rpm:\s*(\d+)', rate_limits_str, re.IGNORECASE)
        tpm_match = re.search(r'tpm:\s*([\d.]+[KkMm]?)', rate_limits_str, re.IGNORECASE)
        rpd_match = re.search(r'rpd:\s*([\d.]+[KkMm]?)', rate_limits_str, re.IGNORECASE)
        tpd_match = re.search(r'tpd:\s*([\d.]+[KkMm]?)', rate_limits_str, re.IGNORECASE)

        if rpm_match:
            result['rpm'] = int(rpm_match.group(1))
        if tpm_match:
            result['tpm'] = parse_token_value(tpm_match.group(1))
        if rpd_match:
            result['rpd'] = parse_token_value(rpd_match.group(1))
        if tpd_match:
            result['tpd'] = parse_token_value(tpd_match.group(1))

        if result['rpm'] is not None:
            return result

    # If no format matched or RPM is null, apply fallback
    if result['rpm'] is None:
        return apply_provider_fallback(result, provider)

    return result
