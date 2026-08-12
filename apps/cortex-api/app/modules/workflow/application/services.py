from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationDomainError
from app.modules.audit.application.services import AuditService
from app.modules.authorization.application.services import AuthorizationService
from app.modules.workflow.domain.entities import (
    WorkflowDefinition,
    WorkflowDefinitionStatus,
    WorkflowExecution,
    WorkflowInstance,
    WorkflowInstanceStatus,
    WorkflowState,
    WorkflowStateType,
    WorkflowTask,
    WorkflowTaskStatus,
    WorkflowTransition,
)
from app.modules.workflow.infrastructure.repositories import (
    WorkflowDefinitionRepository,
    WorkflowExecutionRepository,
    WorkflowInstanceRepository,
    WorkflowStateRepository,
    WorkflowTaskRepository,
    WorkflowTransitionRepository,
)
from app.shared.types import new_id


class WorkflowService:
    def __init__(
        self,
        definition_repo: WorkflowDefinitionRepository,
        state_repo: WorkflowStateRepository,
        transition_repo: WorkflowTransitionRepository,
        instance_repo: WorkflowInstanceRepository,
        task_repo: WorkflowTaskRepository,
        execution_repo: WorkflowExecutionRepository,
        auth_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self.definition_repo = definition_repo
        self.state_repo = state_repo
        self.transition_repo = transition_repo
        self.instance_repo = instance_repo
        self.task_repo = task_repo
        self.execution_repo = execution_repo
        self.auth_service = auth_service
        self.audit_service = audit_service

    # --- Definitions ---
    async def create_definition(
        self, organization_id: str, actor_id: str, name: str, description: str | None = None
    ) -> WorkflowDefinition:
        definition = WorkflowDefinition(
            id=new_id(),
            organization_id=organization_id,
            name=name,
            description=description,
        )
        saved = await self.definition_repo.save(definition)
        await self.audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="user",
            action="workflow.created",
            resource_type="workflow_definition",
            resource_id=saved.id,
            metadata={"name": name},
        )
        return saved

    async def get_definition(self, organization_id: str, definition_id: str) -> WorkflowDefinition:
        definition = await self.definition_repo.get_by_id(definition_id)
        if not definition or definition.organization_id != organization_id:
            raise NotFoundError("Workflow definition not found")
        return definition

    async def list_definitions(self, organization_id: str) -> list[WorkflowDefinition]:
        return await self.definition_repo.list_by_organization(organization_id)

    async def publish_definition(
        self, organization_id: str, actor_id: str, definition_id: str
    ) -> WorkflowDefinition:
        definition = await self.get_definition(organization_id, definition_id)
        if definition.status != WorkflowDefinitionStatus.DRAFT:
            raise ValidationDomainError("Only draft workflows can be published")

        # Validate that it has at least one initial state
        states = await self.state_repo.list_by_definition(definition.id)
        if not any(s.type == WorkflowStateType.INITIAL for s in states):
            raise ValidationDomainError("Workflow must have at least one INITIAL state")

        definition.status = WorkflowDefinitionStatus.PUBLISHED
        saved = await self.definition_repo.save(definition)

        await self.audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="user",
            action="workflow.published",
            resource_type="workflow_definition",
            resource_id=saved.id,
            metadata={"version": saved.version},
        )
        return saved

    # --- States ---
    async def add_state(
        self, organization_id: str, definition_id: str, name: str, key: str, type: WorkflowStateType
    ) -> WorkflowState:
        definition = await self.get_definition(organization_id, definition_id)
        if definition.status != WorkflowDefinitionStatus.DRAFT:
            raise ValidationDomainError("Cannot add states to a published workflow")

        state = WorkflowState(
            id=new_id(),
            workflow_definition_id=definition_id,
            name=name,
            key=key,
            type=type,
        )
        return await self.state_repo.save(state)

    async def list_states(self, organization_id: str, definition_id: str) -> list[WorkflowState]:
        await self.get_definition(organization_id, definition_id)  # ensure it exists
        return await self.state_repo.list_by_definition(definition_id)

    # --- Transitions ---
    async def add_transition(
        self,
        organization_id: str,
        definition_id: str,
        from_state_id: str,
        to_state_id: str,
        action: str,
        required_permission: str | None,
    ) -> WorkflowTransition:
        definition = await self.get_definition(organization_id, definition_id)
        if definition.status != WorkflowDefinitionStatus.DRAFT:
            raise ValidationDomainError("Cannot add transitions to a published workflow")

        # Verify states exist and belong to this definition
        from_state = await self.state_repo.get_by_id(from_state_id)
        to_state = await self.state_repo.get_by_id(to_state_id)
        if not from_state or from_state.workflow_definition_id != definition_id:
            raise NotFoundError("From state not found")
        if not to_state or to_state.workflow_definition_id != definition_id:
            raise NotFoundError("To state not found")

        transition = WorkflowTransition(
            id=new_id(),
            workflow_definition_id=definition_id,
            from_state_id=from_state_id,
            to_state_id=to_state_id,
            action=action,
            required_permission=required_permission,
        )
        return await self.transition_repo.save(transition)

    async def list_transitions(
        self, organization_id: str, definition_id: str
    ) -> list[WorkflowTransition]:
        await self.get_definition(organization_id, definition_id)
        return await self.transition_repo.list_by_definition(definition_id)

    # --- Instances ---
    async def start_instance(
        self,
        organization_id: str,
        actor_id: str,
        definition_id: str,
        resource_type: str,
        resource_id: str,
    ) -> WorkflowInstance:
        definition = await self.get_definition(organization_id, definition_id)
        if definition.status != WorkflowDefinitionStatus.PUBLISHED:
            raise ValidationDomainError("Cannot start an instance of a draft workflow")

        # Check if one already exists for this resource
        existing = await self.instance_repo.get_by_resource(
            organization_id, resource_type, resource_id
        )
        if existing and existing.status == WorkflowInstanceStatus.ACTIVE:
            raise ValidationDomainError(
                "An active workflow instance already exists for this resource"
            )

        states = await self.state_repo.list_by_definition(definition_id)
        initial_states = [s for s in states if s.type == WorkflowStateType.INITIAL]
        if not initial_states:
            raise ValidationDomainError("Workflow definition has no initial state")

        initial_state = initial_states[0]

        instance = WorkflowInstance(
            id=new_id(),
            organization_id=organization_id,
            workflow_definition_id=definition_id,
            current_state_id=initial_state.id,
            resource_type=resource_type,
            resource_id=resource_id,
            started_by=actor_id,
        )
        saved = await self.instance_repo.save(instance)

        # Execution log
        await self.execution_repo.save(
            WorkflowExecution(
                id=new_id(),
                workflow_instance_id=saved.id,
                actor_id=actor_id,
                action="start",
                from_state=None,
                to_state=initial_state.key,
                metadata={"resource_type": resource_type, "resource_id": resource_id},
            )
        )

        await self.audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="user",
            action="workflow.started",
            resource_type="workflow_instance",
            resource_id=saved.id,
            metadata={"workflow_definition_id": definition_id},
        )
        return saved

    async def get_instance(self, organization_id: str, instance_id: str) -> WorkflowInstance:
        instance = await self.instance_repo.get_by_id(instance_id)
        if not instance or instance.organization_id != organization_id:
            raise NotFoundError("Workflow instance not found")
        return instance

    async def execute_transition(
        self,
        organization_id: str,
        actor_id: str,
        instance_id: str,
        action: str,
        metadata: dict[str, Any],
    ) -> WorkflowInstance:
        instance = await self.get_instance(organization_id, instance_id)
        if instance.status != WorkflowInstanceStatus.ACTIVE:
            raise ValidationDomainError(
                f"Cannot transition an instance in {instance.status.value} status"
            )

        transitions = await self.transition_repo.list_by_definition(instance.workflow_definition_id)

        # Find valid transition matching the action and current state
        valid_transitions = [
            t
            for t in transitions
            if t.from_state_id == instance.current_state_id and t.action == action
        ]

        if not valid_transitions:
            raise ValidationDomainError(f"Invalid transition action '{action}' for current state")

        transition = valid_transitions[0]

        # RBAC Check
        if transition.required_permission:
            await self.auth_service.ensure_permission(
                actor_id, organization_id, transition.required_permission
            )

        # Fetch states for logging
        current_state = await self.state_repo.get_by_id(instance.current_state_id)
        next_state = await self.state_repo.get_by_id(transition.to_state_id)
        if not current_state or not next_state:
            raise ValidationDomainError("Corrupted workflow definition: state not found")

        # Apply transition
        instance.current_state_id = transition.to_state_id

        # Check if completion
        if next_state.type == WorkflowStateType.FINAL:
            instance.status = WorkflowInstanceStatus.COMPLETED

        saved = await self.instance_repo.save(instance)

        # Immutable history
        await self.execution_repo.save(
            WorkflowExecution(
                id=new_id(),
                workflow_instance_id=saved.id,
                actor_id=actor_id,
                action=action,
                from_state=current_state.key,
                to_state=next_state.key,
                metadata=metadata,
            )
        )

        await self.audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="user",
            action="workflow.transitioned",
            resource_type="workflow_instance",
            resource_id=saved.id,
            metadata={
                "action": action,
                "from_state": current_state.key,
                "to_state": next_state.key,
            },
        )

        if saved.status == WorkflowInstanceStatus.COMPLETED:
            await self.audit_service.record_action(
                organization_id=organization_id,
                actor_id=actor_id,
                actor_type="user",
                action="workflow.completed",
                resource_type="workflow_instance",
                resource_id=saved.id,
            )

        return saved

    async def list_executions(
        self, organization_id: str, instance_id: str
    ) -> list[WorkflowExecution]:
        await self.get_instance(organization_id, instance_id)
        return await self.execution_repo.list_by_instance(instance_id)

    # --- Tasks ---
    async def create_task(
        self,
        organization_id: str,
        actor_id: str,
        instance_id: str,
        title: str,
        assigned_user_id: str | None = None,
        assigned_role_id: str | None = None,
        due_at: datetime | None = None,
    ) -> WorkflowTask:
        instance = await self.get_instance(organization_id, instance_id)

        task = WorkflowTask(
            id=new_id(),
            workflow_instance_id=instance.id,
            title=title,
            assigned_user_id=assigned_user_id,
            assigned_role_id=assigned_role_id,
            due_at=due_at,
        )
        saved = await self.task_repo.save(task)

        await self.audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="user",
            action="workflow.task_created",
            resource_type="workflow_task",
            resource_id=saved.id,
            metadata={"workflow_instance_id": instance_id},
        )
        return saved

    async def list_tasks(self, organization_id: str, instance_id: str) -> list[WorkflowTask]:
        await self.get_instance(organization_id, instance_id)
        return await self.task_repo.list_by_instance(instance_id)

    async def complete_task(
        self, organization_id: str, actor_id: str, instance_id: str, task_id: str
    ) -> WorkflowTask:
        await self.get_instance(organization_id, instance_id)
        task = await self.task_repo.get_by_id(task_id)
        if not task or task.workflow_instance_id != instance_id:
            raise NotFoundError("Workflow task not found")

        if task.status == WorkflowTaskStatus.COMPLETED:
            raise ValidationDomainError("Task is already completed")

        # Optional: check if actor has role to complete if assigned to role
        # For foundation, if assigned to role, we let the RBAC at the route level handle the broader permissions,
        # but here we can enforce strictly if it's assigned to a specific user.
        if task.assigned_user_id and task.assigned_user_id != actor_id:
            raise ForbiddenError("Task is assigned to another user")

        if task.assigned_role_id:
            membership = await self.auth_service.membership_repo.get_membership(
                organization_id, actor_id
            )
            if not membership:
                raise ForbiddenError("User is not a member of this organization")

            roles = await self.auth_service.get_membership_roles(membership.id)
            if not any(r.id == task.assigned_role_id for r in roles):
                raise ForbiddenError("User does not have the required role to complete this task")

        task.status = WorkflowTaskStatus.COMPLETED
        task.completed_at = datetime.now(UTC)

        saved = await self.task_repo.save(task)

        await self.audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type="user",
            action="workflow.task_completed",
            resource_type="workflow_task",
            resource_id=saved.id,
            metadata={"workflow_instance_id": instance_id},
        )
        return saved
