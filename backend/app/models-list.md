(grep "^class " models.py >> models-list.md)

class Message(SQLModel):
class ProgressSnapshotBase(SQLModel):
class ProgressSnapshotCreate(ProgressSnapshotBase):
class ProgressSnapshotUpdate(SQLModel):
class ProgressSnapshot(ProgressSnapshotBase, table=True):
class ProgressSnapshotPublic(ProgressSnapshotBase):
class ProgressSnapshotsPublic(SQLModel):
class TokenPayload(SQLModel):
class NewPassword(SQLModel):
class Token(SQLModel):
class QualityState(str, Enum):
class QualitySourceType(str, Enum):
class UserBase(SQLModel):
class UserPersonaBase(SQLModel):
class UserPersonaCreate(UserPersonaBase):
class UserPersonaUpdate(SQLModel):
class UserPersona(UserPersonaBase, table=True):
class UserPersonaPublic(UserPersonaBase):
class UserPersonasPublic(SQLModel):
class EventBase(SQLModel):
class StoryBase(SQLModel):
class ItemBase(SQLModel):
class ArchetypeBase(SQLModel):
class PersonaBase(SQLModel):
class TraitBase(SQLModel):
class QualityBase(SQLModel):
class ArchetypeTraitLinkBase(SQLModel):
class PersonaTraitLinkBase(SQLModel):
class ArchetypeQualityLinkBase(SQLModel):
class PersonaQualityLinkBase(SQLModel):
class ArchetypePersonaLinkBase(SQLModel):
class QualityTraitLinkBase(SQLModel):
class PersonaCreate(PersonaBase):
class ArchetypeCreate(ArchetypeBase):
class TraitCreate(TraitBase):
class QualityCreate(QualityBase):
class ItemCreate(ItemBase):
class UserCreate(UserBase):
class EventCreate(EventBase):
class StoryCreate(StoryBase):
class UserBasePartial(SQLModel):
class UserUpdate(UserBasePartial):
class UserUpdateMe(SQLModel):
class UpdatePassword(SQLModel):
class ItemBasePartial(SQLModel):
class ItemUpdate(ItemBasePartial):
class ArchetypeBasePartial(SQLModel):
class ArchetypeUpdate(ArchetypeBasePartial):
class PersonaBasePartial(SQLModel):
class PersonaUpdate(PersonaBasePartial):
class EventBasePartial(SQLModel):
class EventUpdate(EventBasePartial):
class QualityBasePartial(SQLModel):
class QualityUpdate(QualityBasePartial):
class TraitBasePartial(SQLModel):
class TraitUpdate(TraitBasePartial):
class QualityEventTriggerBase(SQLModel):
class QualityEventTrigger(QualityEventTriggerBase, table=True):
class StoryUpdate(SQLModel):
class Story(StoryBase, table=True):
class StoryPublic(StoryBase):
class StoriesPublic(SQLModel):
class StoryNodeBase(SQLModel):
class StoryNodeCreate(StoryNodeBase):
class StoryNodeUpdate(SQLModel):
class StoryNode(StoryNodeBase, table=True):
class StoryNodePublic(StoryNodeBase):
class StoryNodesPublic(SQLModel):
class NodeChoiceBase(SQLModel):
class NodeChoiceCreate(NodeChoiceBase):
class NodeChoiceUpdate(SQLModel):
class NodeChoice(NodeChoiceBase, table=True):
class NodeChoicePublic(NodeChoiceBase):
class NodeChoicesPublic(SQLModel):
class StoryRequirementBase(SQLModel):
class StoryRequirementCreate(StoryRequirementBase):
class StoryRequirementUpdate(SQLModel):
class StoryRequirement(StoryRequirementBase, table=True):
class StoryRequirementPublic(StoryRequirementBase):
class StoryRequirementsPublic(SQLModel):
class UserStoryProgressBase(SQLModel):
class UserStoryProgressCreate(UserStoryProgressBase):
class UserStoryProgressUpdate(SQLModel):
class UserStoryProgress(UserStoryProgressBase, table=True):
class UserStoryProgressPublic(UserStoryProgressBase):
class UserStoryProgressesPublic(SQLModel):
class JumpRequest(SQLModel):
class TimelineEvent(SQLModel):
class Timeline(SQLModel):
class UserNodeChoiceBase(SQLModel):
class UserNodeChoiceCreate(UserNodeChoiceBase):
class UserNodeChoice(UserNodeChoiceBase, table=True):
class UserNodeChoicePublic(UserNodeChoiceBase):
class UserNodeChoicesPublic(SQLModel):
class UserNodeChoiceUpdate(SQLModel):
class ArchetypeTraitLink(ArchetypeTraitLinkBase, table=True):
class ArchetypePersonaLink(ArchetypePersonaLinkBase, table=True):
class ArchetypeQualityLink(ArchetypeQualityLinkBase, table=True):
class PersonaTraitLink(PersonaTraitLinkBase, table=True):
class PersonaQualityLink(PersonaQualityLinkBase, table=True):
class User(UserBase, table=True):
class Item(ItemBase, table=True):
class Event(EventBase, table=True):
class Archetype(ArchetypeBase, table=True):
class Persona(PersonaBase, table=True):
class Quality(QualityBase, table=True):
class Trait(TraitBase, table=True):
class QualityTraitLink(QualityTraitLinkBase, table=True):
class QualityTraitLinkCreate(QualityTraitLinkBase):
class QualityTraitLinkUpdate(SQLModel):
class UserPublic(UserBase):
class ItemPublic(ItemBase):
class EventPublic(EventBase):
class ArchetypePublic(ArchetypeBase):
class PersonaPublic(PersonaBase):
class TraitPublic(TraitBase):
class QualityPublic(QualityBase):
class UsersPublic(SQLModel):
class ItemsPublic(SQLModel):
class EventsPublic(SQLModel):
class ArchetypesPublic(SQLModel):
class PersonasPublic(SQLModel):
class TraitsPublic(SQLModel):
class QualitiesPublic(SQLModel):
class QualityTraitLinkPublic(QualityTraitLinkBase):
class QualityEventTriggerCreate(QualityEventTriggerBase):
class QualityEventTriggerUpdate(SQLModel):
class QualityEventTriggerPublic(QualityEventTriggerBase):
class NodeChoiceBase(SQLModel):
class StoryUserLinkBase(SQLModel):
class StoryBasePartial(SQLModel):
class StoryNodePartial(SQLModel):
class NodeChoiceBasePartial(SQLModel):
class NodeChoicePublic(NodeChoiceBase):
class TagBase(SQLModel):
class TagBasePartial(SQLModel):
class TagPublic(TagBase):
class TagsPublic(SQLModel):
class TagCreate(TagBase):
class TagUpdate(TagBasePartial):
class Tag(TagBase, table=True):
class StoryToTag(SQLModel, table=True):
class StoryPlayBase(SQLModel):
class StoryPlayCreate(StoryPlayBase):
class StoryPlayBasePartial(SQLModel):
class StoryPlayUpdate(StoryPlayBasePartial):
class StoryPlay(StoryPlayBase, table=True):
class StoryPlayPublic(StoryPlayBase):
class StoryPlaysPublic(SQLModel):
class PlayStateBase(SQLModel):
class PlayStateCreate(PlayStateBase):
class PlayStateUpdate(PlayStateBase):
class PlayState(PlayStateBase, table=True):
class PlayStatePublic(PlayStateBase):
class PlayStatesPublic(SQLModel):
class CurrentNodePublic(SQLModel):
class TraitConfigBase(SQLModel):
class TraitConfigBasePartial(SQLModel):
class TraitConfigCreate(TraitConfigBase):
class TraitConfigUpdate(TraitConfigBasePartial):
class TraitConfigPublic(TraitConfigBase):
class TraitConfigsPublic(SQLModel):
class UserRegister(SQLModel):
class RoomBase(SQLModel):
class RoomCreate(RoomBase):
class RoomUpdate(SQLModel):
class Room(RoomBase, table=True):
class RoomPublic(RoomBase):
class RoomsPublic(SQLModel):
class RoomParticipantBase(SQLModel):
class RoomParticipantCreate(RoomParticipantBase):
class RoomParticipantUpdate(SQLModel):
class RoomParticipant(RoomParticipantBase, table=True):
class RoomParticipantPublic(RoomParticipantBase):
class RoomParticipantsPublic(SQLModel):
class ParticipantAddRequest(SQLModel):
class ParticipantRoleChangeRequest(SQLModel):
class MessageResponse(SQLModel):
class RoomMessageBase(SQLModel):
class RoomMessageCreate(RoomMessageBase):
class RoomMessageSend(SQLModel):
class RoomMessageUpdate(SQLModel):
class RoomMessage(RoomMessageBase, table=True):
class RoomMessagePublic(RoomMessageBase):
class RoomMessagesPublic(SQLModel):
class MessageEdit(SQLModel):
class MessageContextToggle(SQLModel):
class RoomEventBase(SQLModel):
class RoomEventCreate(RoomEventBase):
class RoomEvent(RoomEventBase, table=True):
class RoomEventPublic(RoomEventBase):
class RoomEventsPublic(SQLModel):
