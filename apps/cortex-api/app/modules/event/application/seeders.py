from app.modules.workflow.application.services import WorkflowService


async def seed_event_workflow(
    organization_id: str, actor_id: str, workflow_service: WorkflowService
) -> str:
    """
    Seeds a default 'Event Lifecycle' workflow for an organization if it doesn't exist.
    Returns the workflow definition ID.
    """
    definitions = await workflow_service.list_definitions(organization_id)
    event_workflow = next((d for d in definitions if d.name == "Event Lifecycle"), None)

    if event_workflow:
        return event_workflow.id

    # Create Definition
    definition = await workflow_service.create_definition(
        organization_id=organization_id,
        actor_id=actor_id,
        name="Event Lifecycle",
        description="Standard lifecycle for events",
    )
    def_id = definition.id

    from app.modules.workflow.domain.entities import WorkflowStateType

    # Add States
    state_draft = await workflow_service.add_state(
        organization_id, def_id, "Draft", "draft", WorkflowStateType.INITIAL
    )
    state_submitted = await workflow_service.add_state(
        organization_id, def_id, "Submitted", "submitted", WorkflowStateType.NORMAL
    )
    state_approved = await workflow_service.add_state(
        organization_id, def_id, "Approved", "approved", WorkflowStateType.NORMAL
    )
    state_published = await workflow_service.add_state(
        organization_id, def_id, "Published", "published", WorkflowStateType.NORMAL
    )
    state_ongoing = await workflow_service.add_state(
        organization_id, def_id, "Ongoing", "ongoing", WorkflowStateType.NORMAL
    )
    state_completed = await workflow_service.add_state(
        organization_id, def_id, "Completed", "completed", WorkflowStateType.FINAL
    )
    state_archived = await workflow_service.add_state(
        organization_id, def_id, "Archived", "archived", WorkflowStateType.FINAL
    )

    # Add Transitions
    await workflow_service.add_transition(
        organization_id, def_id, state_draft.id, state_submitted.id, "submit", "event.submit"
    )
    await workflow_service.add_transition(
        organization_id, def_id, state_submitted.id, state_approved.id, "approve", "event.approve"
    )
    await workflow_service.add_transition(
        organization_id, def_id, state_submitted.id, state_draft.id, "reject", "event.approve"
    )
    await workflow_service.add_transition(
        organization_id, def_id, state_approved.id, state_published.id, "publish", "event.publish"
    )
    await workflow_service.add_transition(
        organization_id, def_id, state_published.id, state_ongoing.id, "start", "event.manage"
    )
    await workflow_service.add_transition(
        organization_id, def_id, state_ongoing.id, state_completed.id, "complete", "event.manage"
    )

    # Any state to archived
    await workflow_service.add_transition(
        organization_id, def_id, state_draft.id, state_archived.id, "archive", "event.manage"
    )
    await workflow_service.add_transition(
        organization_id, def_id, state_published.id, state_archived.id, "archive", "event.manage"
    )
    await workflow_service.add_transition(
        organization_id, def_id, state_completed.id, state_archived.id, "archive", "event.manage"
    )

    # Publish the definition
    published_def = await workflow_service.publish_definition(organization_id, actor_id, def_id)
    return published_def.id
