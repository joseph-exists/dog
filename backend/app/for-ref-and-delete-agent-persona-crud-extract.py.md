## THIS WILL BE ADDED INTO CRUD.PY FILE ##
## THIS WILL NOT EXIST AS A SEPARATE FILE ##
## DON'T DUPLICATE IMPORTS OR EXISTING FUNCTIONS ##


# Agent Persona CRUD functions


def create_agent_persona(
    *,
    session: Session,
    agent_persona_in: AgentPersonaCreate,
    agent_id: uuid.UUID,
) -> AgentPersona:
    """Create a new agent persona library entry."""
    db_agent_persona = AgentPersona.model_validate(
        agent_persona_in,
        update={"agent_id": agent_id},
    )
    session.add(db_agent_persona)
    session.commit()
    session.refresh(db_agent_persona)
    return db_agent_persona


def get_agent_personas(
    *,
    session: Session,
    agent_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[AgentPersona], int]:
    """Get all agent personas for an agent."""
    count_statement = (
        select(func.count())
        .select_from(AgentPersona)
        .where(AgentPersona.agent_id == agent_id)
    )
    count = session.exec(count_statement).one()

    statement = (
        select(AgentPersona)
        .where(AgentPersona.agent_id == agent_id)
        .offset(skip)
        .limit(limit)
    )
    agent_personas = session.exec(statement).all()
    return list(agent_personas), count


def get_agent_persona(
    *,
    session: Session,
    id: uuid.UUID,
    agent_id: uuid.UUID,
) -> AgentPersona | None:
    """Get an agent persona by ID (scoped to agent_id)."""
    statement = select(AgentPersona).where(
        AgentPersona.id == id,
        AgentPersona.agent_id == agent_id,
    )
    return session.exec(statement).first()


def update_agent_persona(
    *,
    session: Session,
    db_agent_persona: AgentPersona,
    agent_persona_in: AgentPersonaUpdate,
) -> AgentPersona:
    """Update an agent persona."""
    update_data = agent_persona_in.model_dump(exclude_unset=True)
    db_agent_persona.sqlmodel_update(update_data)
    session.add(db_agent_persona)
    session.commit()
    session.refresh(db_agent_persona)
    return db_agent_persona


def delete_agent_persona(*, session: Session, db_agent_persona: AgentPersona) -> None:
    """Delete an agent persona."""
    session.delete(db_agent_persona)
    session.commit()

