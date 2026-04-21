"""
Resource models – ResourceInventory and ResourceRequest.
Admin manages the global resource pool; NGOs submit requests.
"""

import enum
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Enum as SAEnum, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base


class ResourceType(str, enum.Enum):
    FOOD = "food"
    WATER = "water"
    MEDICAL = "medical"
    SHELTER = "shelter"
    CLOTHING = "clothing"
    EQUIPMENT = "equipment"
    TRANSPORT = "transport"
    MONEY = "money"
    OTHERS = "others"


class ResourceStatus(str, enum.Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    DEPLETED = "depleted"
    RESERVED = "reserved"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FULFILLED = "fulfilled"


class ResourceInventory(Base):
    """ORM model for the resource_inventory table. Admin-managed global pool."""

    __tablename__ = "resource_inventory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resource_type = Column(SAEnum(ResourceType, values_callable=lambda obj: [e.value for e in obj]), nullable=False, index=True)
    name = Column(String(255), nullable=False, comment="E.g. 'Rice 5kg bags', 'First Aid Kits'")
    quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=False, default="units", comment="kg, liters, units, sets, etc.")
    location = Column(String(255), nullable=True, comment="Storage location")
    status = Column(SAEnum(ResourceStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=ResourceStatus.AVAILABLE, index=True)
    allocated_to_ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ResourceInventory id={self.id} type={self.resource_type} qty={self.quantity} {self.unit}>"


class ResourceRequest(Base):
    """ORM model for resource_requests table. NGOs request resources from Admin."""

    __tablename__ = "resource_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requesting_ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=False, index=True)
    resource_type = Column(SAEnum(ResourceType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    quantity_requested = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False, default="units")
    reason = Column(Text, nullable=False, comment="Why they need this resource")
    urgency = Column(String(20), nullable=False, default="medium", comment="low|medium|high")
    need_id = Column(Integer, ForeignKey("needs.id"), nullable=True, index=True,
                     comment="Task this resource is needed for (optional)")
    need_description = Column(String(255), nullable=True, comment="Denormalized task title for display")
    status = Column(SAEnum(RequestStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=RequestStatus.PENDING, index=True)
    admin_notes = Column(Text, nullable=True)
    allocated_resource_id = Column(Integer, ForeignKey("resource_inventory.id"), nullable=True,
                                   comment="Which inventory item was allocated")
    quantity_allocated = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<ResourceRequest id={self.id} ngo={self.requesting_ngo_id} status={self.status}>"


class ContributionStatus(str, enum.Enum):
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class InventoryContribution(Base):
    """
    NGO donates items to the Admin's global inventory.
    Admin reviews and merges into existing ResourceInventory on approval.
    """
    __tablename__ = "inventory_contributions"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    contributing_ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=False, index=True)
    resource_type       = Column(SAEnum(ResourceType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    name                = Column(String(255), nullable=False, comment="Must match an existing inventory item name for merge")
    quantity            = Column(Float, nullable=False)
    unit                = Column(String(50), nullable=False, default="units")
    notes               = Column(Text, nullable=True)
    status              = Column(
        SAEnum(ContributionStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default=ContributionStatus.PENDING, index=True,
    )
    admin_notes         = Column(Text, nullable=True)
    merged_into_id      = Column(Integer, ForeignKey("resource_inventory.id"), nullable=True,
                                 comment="Inventory item that received the quantity on approval")
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at         = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<InventoryContribution id={self.id} ngo={self.contributing_ngo_id} status={self.status}>"
