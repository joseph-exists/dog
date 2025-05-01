from sqlmodel import Session

from app.models import Quality
from app.tests.utils.utils import random_lower_string


def create_random_quality(db: Session) -> Quality:
    """
    Create a random quality entry for testing purposes.
    """
    name = random_lower_string()
    description = random_lower_string()

    quality = Quality(
        name=name,
        description=description,
    )
    db.add(quality)
    db.commit()
    db.refresh(quality)
    return quality
