

D: https://pragprog.com/tips/


This is the class where we create the top level database model

class ThingBase(SQLModel):
  title:
  description:

class Thing(ThingBase, table=True):
  id:
  owner_id:
  owner:

class ThingCreate(ThingBase):
  pass

class ThingUpdate(ThingBase):
  title:



class ThingPublic(ThingBase):
  id:
  owner_id:

class ThingsPublic(SQLModel):
  data: list[ThingPublic]
  count: int


def create_quality(*, session: Session, item_in: QualityCreate, owner_id: uuid.UUID) -> Quality:
    db_quality = Quality.model_validate(quality_in, update={"owner_id": owner_id})
    session.add(db_quality)
    session.commit()
    session.refresh(db_quality)
    return db_quality


def create_trait(
    *, session: Session, trait_in: TraitCreate, owner_id: uuid.UUID
) -> Trait:
    db_trait = Trait.model_validate(trait_in, update={"owner_id": owner_id})
    session.add(db_trait)
    session.commit()
    session.refresh(db_trait)
    return db_trait
