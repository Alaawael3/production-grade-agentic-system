"""Declarative base shared by all SQLAlchemy ORM models.

All table models in ``data.schemas`` inherit from ``c`` so
that ``SQLAlchemy.metadata`` tracks every table in a single registry,
enabling a single ``create_all`` / ``drop_all`` call to manage the
full schema.
"""

import os

from sqlalchemy.ext.declarative import declarative_base

SQLAlchemyBase = declarative_base()


def main():
    print(f"welcome from `{os.path.basename(__file__).split('.')[0]}` modeul, nothing to do ^___^!")


if __name__ == "__main__":
    main()
