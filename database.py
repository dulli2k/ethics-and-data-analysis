from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
import nh3
import os

Base = declarative_base()
engine = create_engine("sqlite:///igs_data.db", echo=False)
SessionLocal = sessionmaker(bind=engine)


class CensusTract(Base):
    __tablename__ = "census_tracts"

    id = Column(Integer, primary_key=True, index=True)
    census_tract = Column(String, unique=True, index=True)
    inclusion_score = Column(Float)
    growth_score = Column(Float)
    economy_score = Column(Float)
    community_score = Column(Float)


Base.metadata.create_all(engine)


def _load_csv(path: str) -> pd.DataFrame:
    """
    Load a CSV if it exists, else return empty DataFrame.
    """
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=[
        "census_tract", "inclusion_score", "growth_score",
        "economy_score", "community_score"
    ])


def init_db():
    """
    Import IGS data from one or two CSV files into SQLite.

    - Uses a set to track existing census_tract IDs.
    - Deduplicates rows from a second CSV before inserting.
    """
    # Base CSV (required)
    df_main = _load_csv("igs_data.csv")

    # Optional second CSV for the **challenge**
    df_extra = _load_csv("igs_data_extra.csv")

    # Combine while keeping track of duplicates via sets
    combined_frames = [df_main]
    if not df_extra.empty:
        combined_frames.append(df_extra)

    combined_df = pd.concat(combined_frames, ignore_index=True)

    with SessionLocal() as session:
        # Existing tracts already in DB
        existing_tracts = {
            row.census_tract for row in session.query(CensusTract.census_tract).all()
        }

        # Also track tracts we've inserted during this run
        seen_tracts = set(existing_tracts)

        for _, row in combined_df.iterrows():
            # Get raw value from CSV
            raw_id = str(row["census_tract"])

            # If pandas read it as float (e.g. "6037102107.0"), strip decimals
            if "." in raw_id:
                raw_id = raw_id.split(".")[0]

            # Always store as 11-character zero-padded string
            tract_id_padded = raw_id.zfill(11)

            tract_id_clean = nh3.clean(tract_id_padded)

            # Challenge (set operations) – prevent duplicates
            if tract_id_clean in seen_tracts:
                continue

            seen_tracts.add(tract_id_clean)

            tract = CensusTract(
                census_tract=tract_id_clean,
                inclusion_score=float(row["inclusion_score"]),
                growth_score=float(row["growth_score"]),
                economy_score=float(row["economy_score"]),
                community_score=float(row["community_score"]),
            )
            session.add(tract)

        session.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize DB on import
if __name__ == "__main__":
    init_db()
else:
    # For normal imports (FastAPI/tests)
    init_db()
