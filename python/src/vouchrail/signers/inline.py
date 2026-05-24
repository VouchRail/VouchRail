"""HMAC-SHA256 inline signer — dev / test use only.

Mirrors ``InlineSigner`` in ``packages/sdk/src/signing.ts``. Produces
byte-identical signatures for the same secret + entry hash so a chain
written by one SDK can be verified by the other.
"""

from __future__ import annotations

import hashlib
import hmac

from ..defaults import SIGNING_DEFAULTS
from ..errors import ERROR_CODES, VouchRailSignerError
from .base import Signer


class InlineSigner(Signer):
    key_id = SIGNING_DEFAULTS.inline_key_id

    def __init__(self, secret: str) -> None:
        if not secret or len(secret) < SIGNING_DEFAULTS.inline_secret_min_length:
            raise VouchRailSignerError(
                ERROR_CODES["SIGNER_INVALID_SECRET"],
                f"InlineSigner: secret must be at least "
                f"{SIGNING_DEFAULTS.inline_secret_min_length} characters. "
                f"Inline signing is intended for development only; use a KMS signer in production.",
                {"minLength": SIGNING_DEFAULTS.inline_secret_min_length},
            )
        self._secret = secret.encode("utf-8")

    def sign(self, entry_hash_hex: str) -> str:
        mac = hmac.new(self._secret, entry_hash_hex.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{SIGNING_DEFAULTS.inline_signature_prefix}:{self.key_id}:{mac}"
