  async def list_room_messages(
      *,
      room_id: UUID,
      user_id: UUID,
      active_for_context: bool | None = None,
      is_pinned: bool | None = None,
      sender_type: str | None = None,
      limit: int,
      before: datetime | None,
      session: AsyncSession,
  ) -> RoomMessagesPublic:
      """
      List room_messages from the RoomMessage projection with pagination constraints.
      ...
      """
      # Check membership
      if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
          raise HTTPException(status_code=403, detail="Access denied")

      # ┌─────────────────────────────────────────────────────────────────────┐
      # │ USER JOIN GOES HERE                                                  │
      # │ Join User table to get display names for user-sent messages         │
      # └─────────────────────────────────────────────────────────────────────┘
      query = (
          select(
              RoomMessage,
              User.full_name.label("sender_full_name"),  # ADD: user's full name
              User.email.label("sender_email"),          # ADD: fallback to email
          )
          .outerjoin(User, RoomMessage.sender_id == User.id)  # ADD: LEFT OUTER JOIN
          .where(RoomMessage.room_id == room_id)
          .order_by(RoomMessage.created_at.desc())
          .limit(limit)
      )

      # ┌─────────────────────────────────────────────────────────────────────┐
      # │ FILTERS GO HERE                                                      │
      # │ Apply the optional filters that are already defined in params       │
      # └─────────────────────────────────────────────────────────────────────┘
      if before:
          query = query.where(RoomMessage.created_at < before)

      if active_for_context is not None:  # ADD: filter by context status
          query = query.where(RoomMessage.active_for_context == active_for_context)

      if is_pinned is not None:  # ADD: filter by pinned status
          query = query.where(RoomMessage.is_pinned == is_pinned)

      if sender_type is not None:  # ADD: filter by sender type
          query = query.where(RoomMessage.sender_type == sender_type)

      result = await session.execute(query)

      # ┌─────────────────────────────────────────────────────────────────────┐
      # │ RESULT PROCESSING CHANGES HERE                                       │
      # │ Now we get tuples of (RoomMessage, full_name, email) instead of     │
      # │ just RoomMessage objects                                             │
      # └─────────────────────────────────────────────────────────────────────┘
      rows = result.all()  # CHANGE: .all() instead of .scalars().all()

      # Build response with enriched display names
      messages = []
      for row in rows:
          msg = row[0]  # RoomMessage object
          sender_full_name = row[1]  # User.full_name (or None for agents)
          sender_email = row[2]  # User.email (or None for agents)

          # Compute display name
          if msg.sender_type == "agent":
              display_name = msg.agent_name
          else:
              display_name = sender_full_name or sender_email or "Unknown User"

          # Validate and add display name
          msg_public = RoomMessagePublic.model_validate(msg)
          msg_public.sender_display_name = display_name  # ADD field to model
          messages.append(msg_public)

      # Get total count for this room (consider if filters should apply here too)
      count_result = await session.execute(
          select(func.count()).select_from(RoomMessage).where(RoomMessage.room_id == room_id)
      )
      total_count = count_result.scalar()  # CHANGE: more efficient count query

      return RoomMessagesPublic(
          data=messages,
          count=total_count,
      )

