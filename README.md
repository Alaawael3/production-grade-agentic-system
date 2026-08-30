for schema verioning:
```alembic init src/data/alembic```
and make changes in the env.py
You run:
```alembic revision --autogenerate -m "add user name"```
```alembic upgrade head```



alembic makes verssioning and if we want to call user name and the table have only the user id then alembic will update the table and add name column?

Yes! Exactly. 👍 You got the main idea.

But there is one important detail: Alembic doesn't update the database just because you changed the Python model. It first detects the difference and creates a migration, then you apply that migration.

Let's walk through your exact example.

Initially

Your Python model:

class User(SQLAlchemyBase):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

So your database has:

users
┌──────────────────────┐
│ id                   │
├──────────────────────┤
│ UUID                 │
│ PRIMARY KEY          │
└──────────────────────┘
Then you decide you need a name

You change your Python model:

class User(SQLAlchemyBase):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    name: Mapped[str] = mapped_column(String(100))

Now there is a difference:

Python model                 Database
────────────                 ────────

users                        users
├── id                       └── id
└── name       ← NEW

But the database has NOT changed yet.

Step 1: Ask Alembic to detect the difference

You run:

```alembic revision --autogenerate -m "add user name"```

Alembic compares:

        Python models
             │
             ▼
    SQLAlchemy metadata
             │
             ▼
          Alembic
             │
             │ compare
             ▼
       PostgreSQL

It sees:

Python says:
users has id + name

Database says:
users has id

So Alembic generates a migration that basically says:

def upgrade():
    op.add_column(
        "users",
        sa.Column("name", sa.String(100))
    )
Step 2: Apply the migration

Then you run:

alembic upgrade head

Now Alembic changes the actual database.

Conceptually, it executes:

ALTER TABLE users
ADD COLUMN name VARCHAR(100);

Now:

users
┌──────────────────────┬───────────────┐
│ id                   │ name          │
├──────────────────────┼───────────────┤
│ UUID                 │ VARCHAR(100)  │
└──────────────────────┴───────────────┘

So your Python model and database are synchronized again:

Python                         PostgreSQL
──────                         ──────────

User                           users
│                              │
├── id ───────────────────────→ id
│                              │
└── name ─────────────────────→ name
Why is the "versioning" part important?

Imagine you make 10 changes to your database over 6 months.

Alembic keeps the history:

Migration 1
    ↓
Create users
    ↓
Migration 2
    ↓
Add name
    ↓
Migration 3
    ↓
Add email
    ↓
Migration 4
    ↓
Add created_at

So another developer can clone your project and run:

```alembic upgrade head```

and Alembic knows:

"This database needs migrations 1, 2, 3, and 4."

It applies them in order.