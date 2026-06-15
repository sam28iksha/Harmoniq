from typing import Optional, Annotated
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.staticfiles import StaticFiles
from models import GenreURLChoices, Band, BandCreate, BandUpdate, Album, AuditLog, BandRead
from db import init_db, get_session
from contextlib import asynccontextmanager
from sqlmodel import Session, select, text
from sqlalchemy.orm import selectinload


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)


# =============================================
# BASIC CRUD ENDPOINTS
# =============================================

@app.get('/bands', response_model=list[BandRead])
async def bands(genre: Optional[GenreURLChoices] = None,
                q: Annotated[Optional[str], Query(max_length=10)] = None,
                has_albums: bool = False, session: Session = Depends(get_session)
                ):
    band_list = session.exec(select(Band).options(selectinload(Band.albums))).all()
    if genre:
        band_list = [b for b in band_list if b.genre.value.lower() == genre.value]
    if q:
        band_list = [b for b in band_list if q.lower() in b.name.lower()]
    return band_list

@app.get('/bands/{band_id}', response_model=BandRead)
async def band(band_id: int,
               session: Session = Depends(get_session)
               ):
  band = session.exec(select(Band).where(Band.id == band_id).options(selectinload(Band.albums))).first()
  if band is None:
    raise HTTPException(status_code = 404, detail = 'Band not found')
  return band


# =============================================
# TRANSACTION: Create band with albums (explicit transaction)
# =============================================

@app.post('/bands')
async def create_bands(
   band_data: BandCreate,
   session: Session = Depends(get_session)
   ) -> Band:
    """
    Creates a band and its albums within an EXPLICIT TRANSACTION.
    If any part fails, the entire operation is rolled back.
    """
    try:
        # BEGIN TRANSACTION (explicit)
        session.exec(text("BEGIN"))

        band = Band(name=band_data.name, genre=band_data.genre)
        session.add(band)
        session.flush()  # Get the band ID without committing

        if band_data.albums:
            for album in band_data.albums:
                album_obj = Album(title=album.title, release_date=album.release_date, band=band)
                session.add(album_obj)

        # COMMIT TRANSACTION
        session.exec(text("COMMIT"))
        session.refresh(band)
        return band

    except Exception as e:
        # ROLLBACK TRANSACTION on any error
        session.exec(text("ROLLBACK"))
        raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")


@app.put('/bands/{band_id}')
async def update_band(
    band_id: int,
    band_data: BandUpdate,
    session: Session = Depends(get_session)
) -> Band:
    band = session.get(Band, band_id)
    if band is None:
        raise HTTPException(status_code=404, detail="Band not found")
    
    # Update properties
    if band_data.name is not None:
        band.name = band_data.name
    if band_data.genre is not None:
        band.genre = band_data.genre

    session.add(band)
    session.commit()
    session.refresh(band)
    return band

@app.delete('/bands/{band_id}')
async def delete_band(
    band_id: int,
    session: Session = Depends(get_session)
):
    band = session.get(Band, band_id)
    if band is None:
        raise HTTPException(status_code=404, detail="Band not found")
    session.delete(band)
    session.commit()
    return {"message": "Band deleted successfully"}


# =============================================
# VIEW ENDPOINTS (using SQL Views)
# =============================================

@app.get('/views/rock_bands')
async def get_rock_bands(session: Session = Depends(get_session)):
    """Fetches data from the rock_bands_view SQL VIEW."""
    results = session.exec(text("SELECT * FROM rock_bands_view")).all()
    return [{"id": r[0], "name": r[1], "genre": r[2], "date": r[3]} for r in results]

@app.get('/views/metal_bands')
async def get_metal_bands(session: Session = Depends(get_session)):
    """Fetches data from the metal_bands_view SQL VIEW."""
    results = session.exec(text("SELECT * FROM metal_bands_view")).all()
    return [{"id": r[0], "name": r[1], "genre": r[2], "date": r[3]} for r in results]


# =============================================
# STORED PROCEDURE ENDPOINTS
# =============================================

@app.get('/procedures/bands_by_genre/{genre}')
async def get_bands_by_genre_proc(
    genre: str,
    session: Session = Depends(get_session)
):
    """
    Calls the get_bands_by_genre() STORED PROCEDURE.
    Returns bands of a specific genre along with their album count.
    """
    # Map display genre to PostgreSQL enum name
    genre_map = {
        'rock': 'ROCK', 'electronic': 'ELECTRONIC',
        'metal': 'METAL', 'hip-hop': 'HIP_HOP'
    }
    pg_genre = genre_map.get(genre.lower(), genre.upper())
    result = session.exec(
        text("SELECT * FROM get_bands_by_genre(:genre)"),
        params={"genre": pg_genre}
    ).all()
    return [
        {
            "band_id": r[0],
            "band_name": r[1],
            "band_genre": r[2],
            "album_count": r[3]
        }
        for r in result
    ]

@app.post('/procedures/transfer_albums')
async def transfer_albums_proc(
    from_band_id: int,
    to_band_id: int,
    session: Session = Depends(get_session)
):
    """
    Calls the transfer_albums() STORED PROCEDURE.
    Transfers all albums from one band to another atomically.
    """
    try:
        result = session.exec(
            text("SELECT * FROM transfer_albums(:from_id, :to_id)"),
            params={"from_id": from_band_id, "to_id": to_band_id}
        ).first()
        session.commit()
        return {
            "transferred_count": result[0],
            "from_band": result[1],
            "to_band": result[2]
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# =============================================
# TRANSACTION ENDPOINT (explicit transaction demo)
# =============================================

@app.post('/transactions/bulk_create')
async def bulk_create_bands(
    bands_data: list[BandCreate],
    session: Session = Depends(get_session)
):
    """
    Creates multiple bands with their albums in a SINGLE TRANSACTION.
    If any band creation fails, ALL bands are rolled back.
    Demonstrates explicit BEGIN / COMMIT / ROLLBACK.
    """
    created_bands = []
    try:
        # BEGIN TRANSACTION
        session.exec(text("BEGIN"))

        for band_data in bands_data:
            band = Band(name=band_data.name, genre=band_data.genre)
            session.add(band)
            session.flush()  # Get band ID

            if band_data.albums:
                for album in band_data.albums:
                    album_obj = Album(
                        title=album.title,
                        release_date=album.release_date,
                        band=band
                    )
                    session.add(album_obj)

            created_bands.append({"id": band.id, "name": band.name})

        # COMMIT TRANSACTION — all bands created successfully
        session.exec(text("COMMIT"))
        return {
            "message": f"Successfully created {len(created_bands)} bands in a single transaction",
            "bands": created_bands
        }

    except Exception as e:
        # ROLLBACK TRANSACTION — none of the bands are created
        session.exec(text("ROLLBACK"))
        raise HTTPException(
            status_code=500,
            detail=f"Transaction rolled back. No bands were created. Error: {str(e)}"
        )


# =============================================
# AUDIT LOG ENDPOINT (populated by triggers)
# =============================================

@app.get('/logs')
async def get_logs(session: Session = Depends(get_session)) -> list[AuditLog]:
    """Returns audit logs populated automatically by database TRIGGERS."""
    logs = session.exec(select(AuditLog).order_by(AuditLog.timestamp.desc())).all()
    return logs


# =============================================
# STATIC FILES (Frontend)
# =============================================

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
