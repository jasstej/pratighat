"""
Pratighat.ai — Hierarchy Schemas
Hierarchy-aware schemas for formations, units, sites, networks with
nested children/parent data and aggregate counts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class FormationBriefWithChildren(BaseModel):
    """Formation with direct children list."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    code: Optional[str] = None
    status: str = "active"
    children: List["FormationBriefWithChildren"] = []
    unit_count: int = 0
    site_count: int = 0
    network_count: int = 0
    asset_count: int = 0


class UnitBriefWithParent(BaseModel):
    """Unit with parent information."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    code: Optional[str] = None
    status: str = "active"
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    formation_id: Optional[int] = None
    site_count: int = 0
    network_count: int = 0
    asset_count: int = 0


class HierarchyNode(BaseModel):
    """A single node in the org hierarchy tree."""
    id: int
    type: str  # formation | unit | site | network | asset
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    parent_type: Optional[str] = None
    children: List["HierarchyNode"] = []
    metadata: Optional[Dict[str, Any]] = None


class HierarchyTree(BaseModel):
    """Full organization hierarchy starting from formations."""
    organization_id: int
    organization_name: str
    organization_slug: str
    formations: List[HierarchyNode] = []
    total_formations: int = 0
    total_units: int = 0
    total_sites: int = 0
    total_networks: int = 0
    total_assets: int = 0


class SiteWithNetworkCount(BaseModel):
    """Site with network and asset counts."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    physical_address: Optional[str] = None
    status: str = "active"
    network_count: int = 0
    asset_count: int = 0


class NetworkWithAssetCount(BaseModel):
    """Network with asset count."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    cidr: Optional[str] = None
    status: str = "active"
    asset_count: int = 0


# Type alias for re-export
FormationBriefRecursive = FormationBriefWithChildren
