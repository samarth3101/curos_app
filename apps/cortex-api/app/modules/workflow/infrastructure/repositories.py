"""Repositories for the Workflow module."""

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.modules.workflow.domain.entities import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowInstance,
    WorkflowState,
    WorkflowTask,
    WorkflowTransition,
)
from app.modules.workflow.infrastructure.models import (
    WorkflowDefinitionModel,
    WorkflowExecutionModel,
    WorkflowInstanceModel,
    WorkflowStateModel,
    WorkflowTaskModel,
    WorkflowTransitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class WorkflowDefinitionRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: WorkflowDefinitionModel) -> WorkflowDefinition:
        return WorkflowDefinition(
            id=model.id,
            organization_id=model.organization_id,
            name=model.name,
            description=model.description,
            version=model.version,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: WorkflowDefinition) -> WorkflowDefinitionModel:
        return WorkflowDefinitionModel(
            id=entity.id,
            organization_id=entity.organization_id,
            name=entity.name,
            description=entity.description,
            version=entity.version,
            status=entity.status.value,
        )

    async def get_by_id(self, definition_id: str) -> WorkflowDefinition | None:
        stmt = select(WorkflowDefinitionModel).where(WorkflowDefinitionModel.id == definition_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: WorkflowDefinition) -> WorkflowDefinition:
        model = await self.session.get(WorkflowDefinitionModel, entity.id)
        if model:
            model.name = entity.name
            model.description = entity.description
            model.version = entity.version
            model.status = entity.status.value
        else:
            model = self._to_model(entity)
            self.session.add(model)
        await self.session.flush()

        # reload updated_at etc
        await self.session.refresh(model)
        return self._to_entity(model)

    async def list_by_organization(self, organization_id: str) -> list[WorkflowDefinition]:
        stmt = (
            select(WorkflowDefinitionModel)
            .where(WorkflowDefinitionModel.organization_id == organization_id)
            .order_by(WorkflowDefinitionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]


class WorkflowStateRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: WorkflowStateModel) -> WorkflowState:
        return WorkflowState(
            id=model.id,
            workflow_definition_id=model.workflow_definition_id,
            name=model.name,
            key=model.key,
            type=model.type,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, state_id: str) -> WorkflowState | None:
        stmt = select(WorkflowStateModel).where(WorkflowStateModel.id == state_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: WorkflowState) -> WorkflowState:
        model = await self.session.get(WorkflowStateModel, entity.id)
        if model:
            model.name = entity.name
            model.key = entity.key
            model.type = entity.type.value
        else:
            model = WorkflowStateModel(
                id=entity.id,
                workflow_definition_id=entity.workflow_definition_id,
                name=entity.name,
                key=entity.key,
                type=entity.type.value,
            )
            self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def list_by_definition(self, definition_id: str) -> list[WorkflowState]:
        stmt = select(WorkflowStateModel).where(
            WorkflowStateModel.workflow_definition_id == definition_id
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]


class WorkflowTransitionRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: WorkflowTransitionModel) -> WorkflowTransition:
        return WorkflowTransition(
            id=model.id,
            workflow_definition_id=model.workflow_definition_id,
            from_state_id=model.from_state_id,
            to_state_id=model.to_state_id,
            action=model.action,
            required_permission=model.required_permission,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, transition_id: str) -> WorkflowTransition | None:
        model = await self.session.get(WorkflowTransitionModel, transition_id)
        return self._to_entity(model) if model else None

    async def save(self, entity: WorkflowTransition) -> WorkflowTransition:
        model = await self.session.get(WorkflowTransitionModel, entity.id)
        if model:
            model.from_state_id = entity.from_state_id
            model.to_state_id = entity.to_state_id
            model.action = entity.action
            model.required_permission = entity.required_permission
        else:
            model = WorkflowTransitionModel(
                id=entity.id,
                workflow_definition_id=entity.workflow_definition_id,
                from_state_id=entity.from_state_id,
                to_state_id=entity.to_state_id,
                action=entity.action,
                required_permission=entity.required_permission,
            )
            self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def list_by_definition(self, definition_id: str) -> list[WorkflowTransition]:
        stmt = select(WorkflowTransitionModel).where(
            WorkflowTransitionModel.workflow_definition_id == definition_id
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]


class WorkflowInstanceRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: WorkflowInstanceModel) -> WorkflowInstance:
        return WorkflowInstance(
            id=model.id,
            organization_id=model.organization_id,
            workflow_definition_id=model.workflow_definition_id,
            current_state_id=model.current_state_id,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            started_by=model.started_by,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, instance_id: str) -> WorkflowInstance | None:
        model = await self.session.get(WorkflowInstanceModel, instance_id)
        return self._to_entity(model) if model else None

    async def get_by_resource(
        self, organization_id: str, resource_type: str, resource_id: str
    ) -> WorkflowInstance | None:
        stmt = select(WorkflowInstanceModel).where(
            WorkflowInstanceModel.organization_id == organization_id,
            WorkflowInstanceModel.resource_type == resource_type,
            WorkflowInstanceModel.resource_id == resource_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: WorkflowInstance) -> WorkflowInstance:
        model = await self.session.get(WorkflowInstanceModel, entity.id)
        if model:
            model.current_state_id = entity.current_state_id
            model.status = entity.status.value
        else:
            model = WorkflowInstanceModel(
                id=entity.id,
                organization_id=entity.organization_id,
                workflow_definition_id=entity.workflow_definition_id,
                current_state_id=entity.current_state_id,
                resource_type=entity.resource_type,
                resource_id=entity.resource_id,
                started_by=entity.started_by,
                status=entity.status.value,
            )
            self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)


class WorkflowTaskRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: WorkflowTaskModel) -> WorkflowTask:
        return WorkflowTask(
            id=model.id,
            workflow_instance_id=model.workflow_instance_id,
            title=model.title,
            assigned_user_id=model.assigned_user_id,
            assigned_role_id=model.assigned_role_id,
            status=model.status,
            due_at=model.due_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, task_id: str) -> WorkflowTask | None:
        model = await self.session.get(WorkflowTaskModel, task_id)
        return self._to_entity(model) if model else None

    async def save(self, entity: WorkflowTask) -> WorkflowTask:
        model = await self.session.get(WorkflowTaskModel, entity.id)
        if model:
            model.status = entity.status.value
            model.completed_at = entity.completed_at
            model.title = entity.title
            model.assigned_user_id = entity.assigned_user_id
            model.assigned_role_id = entity.assigned_role_id
            model.due_at = entity.due_at
        else:
            model = WorkflowTaskModel(
                id=entity.id,
                workflow_instance_id=entity.workflow_instance_id,
                title=entity.title,
                assigned_user_id=entity.assigned_user_id,
                assigned_role_id=entity.assigned_role_id,
                status=entity.status.value,
                due_at=entity.due_at,
                completed_at=entity.completed_at,
            )
            self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def list_by_instance(self, instance_id: str) -> list[WorkflowTask]:
        stmt = select(WorkflowTaskModel).where(
            WorkflowTaskModel.workflow_instance_id == instance_id
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]


class WorkflowExecutionRepository:
    """Immutable log of workflow transitions."""

    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: WorkflowExecutionModel) -> WorkflowExecution:
        return WorkflowExecution(
            id=model.id,
            workflow_instance_id=model.workflow_instance_id,
            actor_id=model.actor_id,
            action=model.action,
            from_state=model.from_state,
            to_state=model.to_state,
            metadata=model.metadata_,
            timestamp=model.timestamp,
        )

    async def save(self, entity: WorkflowExecution) -> WorkflowExecution:
        model = WorkflowExecutionModel(
            id=entity.id,
            workflow_instance_id=entity.workflow_instance_id,
            actor_id=entity.actor_id,
            action=entity.action,
            from_state=entity.from_state,
            to_state=entity.to_state,
            metadata_=entity.metadata,
            timestamp=entity.timestamp,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def list_by_instance(self, instance_id: str) -> list[WorkflowExecution]:
        stmt = (
            select(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.workflow_instance_id == instance_id)
            .order_by(WorkflowExecutionModel.timestamp.asc())
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]
