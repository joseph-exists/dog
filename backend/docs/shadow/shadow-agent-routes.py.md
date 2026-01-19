
# from backend/app/api/routes/agent_routes.py

in create_agent:

        # Shadow versioning (non-blocking - skips if user not set up)
        try:
            version = shadow_service.create_entity_version(
                session=session,
                user=current_user,
                entity_type="agent",
                entity_id=config.id,
                entity_data=config.model_dump(mode="json"),
                message=f"Create agent: {config.name}",
            )
            if version:
                logger.info(f"Shadow version {version.version_number} created for agent {config.slug}")
        except Exception as e:
            logger.warning(f"Shadow versioning failed for agent {config.slug}: {e}")
