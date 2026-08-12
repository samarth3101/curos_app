from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.shared.base_model import Base
from app.modules.workflow.domain.entities import (
    WorkflowDefinitionStatus,
    WorkflowStateType,
    WorkflowInstanceStatus,
    WorkflowTaskStatus,
)


class WorkflowDefinitionModel(Base):
    __tablename__ = "workflow_definitions"

    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(SQLEnum(WorkflowDefinitionStatus), nullable=False, default=WorkflowDefinitionStatus.DRAFT)
    
    states = relationship("WorkflowStateModel", back_populates="definition", cascade="all, delete-orphan", passive_deletes=True)
    transitions = relationship("WorkflowTransitionModel", back_populates="definition", cascade="all, delete-orphan", passive_deletes=True)
    instances = relationship("WorkflowInstanceModel", back_populates="definition")


class WorkflowStateModel(Base):
    __tablename__ = "workflow_states"

    id = Column(String(36), primary_key=True)
    workflow_definition_id = Column(String(36), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    key = Column(String(100), nullable=False)
    type = Column(SQLEnum(WorkflowStateType), nullable=False, default=WorkflowStateType.NORMAL)
    
    definition = relationship("WorkflowDefinitionModel", back_populates="states")


class WorkflowTransitionModel(Base):
    __tablename__ = "workflow_transitions"

    id = Column(String(36), primary_key=True)
    workflow_definition_id = Column(String(36), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), index=True, nullable=False)
    from_state_id = Column(String(36), ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False)
    to_state_id = Column(String(36), ForeignKey("workflow_states.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False)
    required_permission = Column(String(100), nullable=True)

    definition = relationship("WorkflowDefinitionModel", back_populates="transitions")
    from_state = relationship("WorkflowStateModel", foreign_keys=[from_state_id])
    to_state = relationship("WorkflowStateModel", foreign_keys=[to_state_id])


class WorkflowInstanceModel(Base):
    __tablename__ = "workflow_instances"

    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workflow_definition_id = Column(String(36), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), index=True, nullable=False)
    current_state_id = Column(String(36), ForeignKey("workflow_states.id"), nullable=False)
    resource_type = Column(String(100), index=True, nullable=False)
    resource_id = Column(String(36), index=True, nullable=False)
    started_by = Column(String(36), nullable=False)
    status = Column(SQLEnum(WorkflowInstanceStatus), nullable=False, default=WorkflowInstanceStatus.ACTIVE)

    definition = relationship("WorkflowDefinitionModel", back_populates="instances")
    current_state = relationship("WorkflowStateModel", foreign_keys=[current_state_id])
    tasks = relationship("WorkflowTaskModel", back_populates="instance")


class WorkflowTaskModel(Base):
    __tablename__ = "workflow_tasks"

    id = Column(String(36), primary_key=True)
    workflow_instance_id = Column(String(36), ForeignKey("workflow_instances.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    assigned_user_id = Column(String(36), ForeignKey("identity_users.id", ondelete="SET NULL"), index=True, nullable=True)
    assigned_role_id = Column(String(36), ForeignKey("roles.id", ondelete="SET NULL"), index=True, nullable=True)
    status = Column(SQLEnum(WorkflowTaskStatus), nullable=False, default=WorkflowTaskStatus.PENDING)
    due_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    instance = relationship("WorkflowInstanceModel", back_populates="tasks")


class WorkflowExecutionModel(Base):
    __tablename__ = "workflow_executions"

    id = Column(String(36), primary_key=True)
    workflow_instance_id = Column(String(36), ForeignKey("workflow_instances.id", ondelete="CASCADE"), index=True, nullable=False)
    actor_id = Column(String(36), nullable=False)
    action = Column(String(100), nullable=False)
    from_state = Column(String(100), nullable=True)  # Store state keys, not IDs, since it's immutable history
    to_state = Column(String(100), nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    timestamp = Column(DateTime(timezone=True), nullable=False)
