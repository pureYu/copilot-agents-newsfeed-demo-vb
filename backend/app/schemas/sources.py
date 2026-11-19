import ipaddress
from datetime import datetime
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

from app.models import SourceType

# Domains that must never be used as source URLs (SSRF guard).
_BLOCKED_HOSTS: frozenset[str] = frozenset({"localhost"})
_BLOCKED_SUFFIXES: tuple[str, ...] = (".local", ".internal", ".localhost", ".intranet", ".corp")


class SourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: AnyHttpUrl
    source_type: SourceType
    config: dict = Field(default_factory=dict)
    enabled: bool = True

    @field_validator("url")
    @classmethod
    def url_must_be_public(cls, v: AnyHttpUrl) -> AnyHttpUrl:
        """Reject URLs targeting private or reserved addresses (SSRF mitigation).

        IP addresses are checked against Python's ipaddress.is_global.  Domain
        names are checked against a blocklist of known-internal patterns.  DNS
        resolution is intentionally NOT performed here — use network egress
        controls (firewall / VPC policy) as the defence-in-depth layer.
        """
        host = urlparse(str(v)).hostname or ""
        if not host:
            raise ValueError("URL must contain a valid hostname.")

        try:
            addr = ipaddress.ip_address(host)
        except ValueError:
            addr = None  # hostname is a domain name, not a bare IP

        if addr is not None:
            if not addr.is_global:
                raise ValueError(
                    f"URL must resolve to a public address; "
                    f"{host!r} is in a private, loopback, or reserved range."
                )
        else:
            if host.lower() in _BLOCKED_HOSTS or any(
                host.lower().endswith(s) for s in _BLOCKED_SUFFIXES
            ):
                raise ValueError(
                    f"URL must not target an internal or reserved domain ({host!r})."
                )

        return v


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    config: dict | None = None
    enabled: bool | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    source_type: SourceType
    config: dict
    enabled: bool
    created_at: datetime
    updated_at: datetime


class SourceListResponse(BaseModel):
    items: list[SourceResponse]
    total: int
