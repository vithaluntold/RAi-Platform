"""
Agent Service — business logic for agent CRUD, task linking, and execution.

Provider abstraction:
  The service layer is provider-agnostic.  It stores whatever backend_config
  the caller sends, tagged with provider_type + backend_provider so the
  runtime dispatch layer (future) can route to Azure / LLMLite / hybrid.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.agent import (
    Agent, AgentType, AgentStatus, ProviderType,
    WorkflowTaskAgent,
    AssignmentTaskAgent, AgentAssignmentStatus,
    AgentExecution, ExecutionStatus,
)


class AgentService:
    """Handles agent CRUD operations"""

    @staticmethod
    def create_agent(db: Session, payload: dict, created_by: uuid.UUID) -> Agent:
        """Create a new agent definition"""
        agent_type_value = payload.get("agent_type", "custom")
        try:
            agent_type_enum = AgentType(agent_type_value)
        except ValueError:
            agent_type_enum = AgentType.CUSTOM

        provider_type_value = payload.get("provider_type", "external")
        try:
            provider_type_enum = ProviderType(provider_type_value)
        except ValueError:
            provider_type_enum = ProviderType.EXTERNAL

        agent = Agent(
            name=payload["name"],
            description=payload.get("description"),
            version=payload.get("version", "1.0.0"),
            agent_type=agent_type_enum,
            provider_type=provider_type_enum,
            backend_provider=payload.get("backend_provider", "azure"),
            backend_config=payload.get("backend_config"),
            external_url=payload.get("external_url"),
            capabilities=payload.get("capabilities"),
            input_schema=payload.get("input_schema"),
            output_schema=payload.get("output_schema"),
            organization_id=payload.get("organization_id"),
            status=AgentStatus.ACTIVE,
            is_system=False,
            created_by=created_by,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def get_agent(db: Session, agent_id: uuid.UUID) -> Optional[Agent]:
        """Get a single agent by ID"""
        return db.query(Agent).filter(Agent.id == agent_id).first()

    @staticmethod
    def list_agents(
        db: Session,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        provider_type: Optional[str] = None,
        backend_provider: Optional[str] = None,
    ) -> list:
        """List agents with optional filters"""
        query = db.query(Agent)
        if agent_type:
            try:
                query = query.filter(Agent.agent_type == AgentType(agent_type))
            except ValueError:
                pass
        if status:
            try:
                query = query.filter(Agent.status == AgentStatus(status))
            except ValueError:
                pass
        if provider_type:
            try:
                query = query.filter(Agent.provider_type == ProviderType(provider_type))
            except ValueError:
                pass
        if backend_provider:
            query = query.filter(Agent.backend_provider == backend_provider)
        return query.order_by(Agent.name).all()

    @staticmethod
    def update_agent(db: Session, agent_id: uuid.UUID, payload: dict) -> Optional[Agent]:
        """Update an agent definition"""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        for field in ["name", "description", "version", "backend_provider",
                       "backend_config", "external_url",
                       "capabilities", "input_schema", "output_schema"]:
            if field in payload and payload[field] is not None:
                setattr(agent, field, payload[field])

        if "agent_type" in payload and payload["agent_type"] is not None:
            try:
                agent.agent_type = AgentType(payload["agent_type"])
            except ValueError:
                pass

        if "provider_type" in payload and payload["provider_type"] is not None:
            try:
                agent.provider_type = ProviderType(payload["provider_type"])
            except ValueError:
                pass

        if "status" in payload and payload["status"] is not None:
            try:
                agent.status = AgentStatus(payload["status"])
            except ValueError:
                pass

        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def delete_agent(db: Session, agent_id: uuid.UUID) -> bool:
        """Delete an agent (soft delete by marking inactive)"""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False
        agent.status = AgentStatus.INACTIVE
        db.commit()
        return True


class WorkflowTaskAgentService:
    """Handles attaching agents to workflow template tasks"""

    @staticmethod
    def attach_agent(db: Session, task_id: uuid.UUID, payload: dict) -> WorkflowTaskAgent:
        """Attach an agent to a workflow template task"""
        wta = WorkflowTaskAgent(
            task_id=task_id,
            agent_id=payload["agent_id"],
            position=payload.get("position", 0),
            is_required=payload.get("is_required", False),
            task_config=payload.get("task_config"),
            instructions=payload.get("instructions"),
        )
        db.add(wta)
        db.commit()
        db.refresh(wta)
        return wta

    @staticmethod
    def list_task_agents(db: Session, task_id: uuid.UUID) -> list:
        """List all agents attached to a workflow template task"""
        return (
            db.query(WorkflowTaskAgent)
            .filter(WorkflowTaskAgent.task_id == task_id)
            .order_by(WorkflowTaskAgent.position)
            .all()
        )

    @staticmethod
    def update_task_agent(
        db: Session, wta_id: uuid.UUID, payload: dict
    ) -> Optional[WorkflowTaskAgent]:
        """Update agent config on a template task"""
        wta = db.query(WorkflowTaskAgent).filter(WorkflowTaskAgent.id == wta_id).first()
        if not wta:
            return None

        for field in ["position", "is_required", "task_config", "instructions"]:
            if field in payload and payload[field] is not None:
                setattr(wta, field, payload[field])

        db.commit()
        db.refresh(wta)
        return wta

    @staticmethod
    def remove_task_agent(db: Session, wta_id: uuid.UUID) -> bool:
        """Remove an agent from a workflow template task"""
        wta = db.query(WorkflowTaskAgent).filter(WorkflowTaskAgent.id == wta_id).first()
        if not wta:
            return False
        db.delete(wta)
        db.commit()
        return True


class AssignmentTaskAgentService:
    """Handles agent assignments at the instance (assignment) level"""

    @staticmethod
    def clone_from_template(
        db: Session,
        assignment_task_id: uuid.UUID,
        template_task_id: uuid.UUID,
        assigned_by: uuid.UUID,
    ) -> list:
        """
        Clone all template task agents into assignment task agents.
        Called during assignment activation (deep clone).
        """
        template_agents = (
            db.query(WorkflowTaskAgent)
            .filter(WorkflowTaskAgent.task_id == template_task_id)
            .order_by(WorkflowTaskAgent.position)
            .all()
        )

        cloned = []
        for ta in template_agents:
            ata = AssignmentTaskAgent(
                task_id=assignment_task_id,
                agent_id=ta.agent_id,
                template_agent_id=ta.id,
                order=ta.position,
                status=AgentAssignmentStatus.PENDING,
                is_required=ta.is_required,
                task_config=ta.task_config,
                instructions=ta.instructions,
                assigned_by=assigned_by,
            )
            db.add(ata)
            cloned.append(ata)

        db.commit()
        for item in cloned:
            db.refresh(item)
        return cloned

    @staticmethod
    def assign_agent(
        db: Session, task_id: uuid.UUID, payload: dict, assigned_by: uuid.UUID
    ) -> AssignmentTaskAgent:
        """Manually assign an agent to an assignment task"""
        ata = AssignmentTaskAgent(
            task_id=task_id,
            agent_id=payload["agent_id"],
            order=payload.get("order", 0),
            status=AgentAssignmentStatus.PENDING,
            is_required=payload.get("is_required", False),
            task_config=payload.get("task_config"),
            instructions=payload.get("instructions"),
            assigned_by=assigned_by,
        )
        db.add(ata)
        db.commit()
        db.refresh(ata)
        return ata

    @staticmethod
    def list_task_agents(db: Session, task_id: uuid.UUID) -> list:
        """List all agents assigned to an assignment task"""
        return (
            db.query(AssignmentTaskAgent)
            .filter(AssignmentTaskAgent.task_id == task_id)
            .order_by(AssignmentTaskAgent.order)
            .all()
        )

    @staticmethod
    def update_task_agent(
        db: Session, ata_id: uuid.UUID, payload: dict
    ) -> Optional[AssignmentTaskAgent]:
        """Update agent assignment on an assignment task"""
        ata = db.query(AssignmentTaskAgent).filter(AssignmentTaskAgent.id == ata_id).first()
        if not ata:
            return None

        for field in ["order", "is_required", "task_config", "instructions"]:
            if field in payload and payload[field] is not None:
                setattr(ata, field, payload[field])

        if "status" in payload and payload["status"] is not None:
            try:
                ata.status = AgentAssignmentStatus(payload["status"])
            except ValueError:
                pass

        db.commit()
        db.refresh(ata)
        return ata

    @staticmethod
    def remove_task_agent(db: Session, ata_id: uuid.UUID) -> bool:
        """Remove an agent from an assignment task"""
        ata = db.query(AssignmentTaskAgent).filter(AssignmentTaskAgent.id == ata_id).first()
        if not ata:
            return False
        db.delete(ata)
        db.commit()
        return True


class AgentExecutionService:
    """Handles agent execution tracking"""

    @staticmethod
    def create_execution(
        db: Session,
        assignment_task_agent_id: uuid.UUID,
        triggered_by: uuid.UUID,
        input_data: Optional[dict] = None,
    ) -> AgentExecution:
        """Create a new execution record when an agent is triggered"""
        ata = (
            db.query(AssignmentTaskAgent)
            .filter(AssignmentTaskAgent.id == assignment_task_agent_id)
            .first()
        )
        if not ata:
            raise ValueError("Assignment task agent not found")

        agent = db.query(Agent).filter(Agent.id == ata.agent_id).first()

        execution = AgentExecution(
            assignment_task_agent_id=assignment_task_agent_id,
            agent_id=ata.agent_id,
            task_id=ata.task_id,
            triggered_by=triggered_by,
            status=ExecutionStatus.QUEUED,
            input_data=input_data,
            backend_provider=agent.backend_provider if agent else None,
        )
        db.add(execution)
        db.flush()

        ata.status = AgentAssignmentStatus.RUNNING
        ata.last_run_at = datetime.utcnow()
        ata.last_execution_id = execution.id

        db.commit()
        db.refresh(execution)

        return execution

    @staticmethod
    def start_execution(db: Session, execution_id: uuid.UUID) -> Optional[AgentExecution]:
        """Mark execution as started"""
        execution = db.query(AgentExecution).filter(AgentExecution.id == execution_id).first()
        if not execution:
            return None
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.utcnow()
        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def complete_execution(
        db: Session,
        execution_id: uuid.UUID,
        output_data: Optional[dict] = None,
    ) -> Optional[AgentExecution]:
        """Mark execution as completed with results"""
        execution = db.query(AgentExecution).filter(AgentExecution.id == execution_id).first()
        if not execution:
            return None

        now = datetime.utcnow()
        execution.status = ExecutionStatus.COMPLETED
        execution.output_data = output_data
        execution.completed_at = now
        if execution.started_at:
            execution.duration_seconds = (now - execution.started_at).total_seconds()

        ata = (
            db.query(AssignmentTaskAgent)
            .filter(AssignmentTaskAgent.id == execution.assignment_task_agent_id)
            .first()
        )
        if ata:
            ata.status = AgentAssignmentStatus.COMPLETED

        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def fail_execution(
        db: Session,
        execution_id: uuid.UUID,
        error_message: str,
        error_details: Optional[dict] = None,
    ) -> Optional[AgentExecution]:
        """Mark execution as failed"""
        execution = db.query(AgentExecution).filter(AgentExecution.id == execution_id).first()
        if not execution:
            return None

        now = datetime.utcnow()
        execution.status = ExecutionStatus.FAILED
        execution.error_message = error_message
        execution.error_details = error_details
        execution.completed_at = now
        if execution.started_at:
            execution.duration_seconds = (now - execution.started_at).total_seconds()

        ata = (
            db.query(AssignmentTaskAgent)
            .filter(AssignmentTaskAgent.id == execution.assignment_task_agent_id)
            .first()
        )
        if ata:
            ata.status = AgentAssignmentStatus.FAILED

        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def list_executions(
        db: Session, assignment_task_agent_id: uuid.UUID
    ) -> list:
        """List all executions for an assignment task agent"""
        return (
            db.query(AgentExecution)
            .filter(AgentExecution.assignment_task_agent_id == assignment_task_agent_id)
            .order_by(AgentExecution.created_at.desc())
            .all()
        )

    @staticmethod
    def get_execution(db: Session, execution_id: uuid.UUID) -> Optional[AgentExecution]:
        """Get a single execution"""
        return db.query(AgentExecution).filter(AgentExecution.id == execution_id).first()
