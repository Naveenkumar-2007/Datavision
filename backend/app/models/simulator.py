"""
Scenario Simulator Models — What-if scenario analysis, Monte Carlo simulations, and stress testing.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Text, Integer, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Simulation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """What-if scenario simulation definition."""

    __tablename__ = "simulations"
    __table_args__ = (
        Index("ix_simulations_user_id", "user_id"),
        Index("ix_simulations_name", "name"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    simulation_type: Mapped[str] = mapped_column(String(50), default="monte_carlo", nullable=False)  # monte_carlo, sensitivity, stress_test
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    versions: Mapped[list["SimulationVersion"]] = relationship(
        back_populates="simulation", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Simulation name={self.name} type={self.simulation_type}>"


class SimulationVersion(UUIDPrimaryKeyMixin, Base):
    """Historical version snapshot of a scenario simulation."""

    __tablename__ = "simulation_versions"

    simulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    config_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    results_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default="now()", nullable=False)

    # Relationships
    simulation: Mapped["Simulation"] = relationship(back_populates="versions")

    def __repr__(self) -> str:
        return f"<SimulationVersion sim={self.simulation_id} v={self.version_number}>"
