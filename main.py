from typing import Optional, Annotated
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.staticfiles import StaticFiles
from models import GenreURLChoices, Band, BandCreate, BandUpdate, Album, AuditLog
from db import init_db, get_session
from contextlib import asynccontextmanager
from sqlmodel import Session, select, text


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

#@app.get('/') #ROUTE
#async def index() -> dict[str, str]: #ASYNC FUNCTION WITH PROPER RETURN TYPE
#    return {'hello': 'world'}

#@app.get('/about')
#async def about() -> str:
#    return 'AN EXCEPTIONAL COMPANY'


#class GenreURLChoices(Enum):    #TO SET ONLY POSSIBLE OPTIONS IN THE ROUTE
#    ROCK = 'rock'
#    ELECTRONIC = 'electronic'
#    METAL = 'metal'
#    HIP_HOP = 'hip-hop'


#Demo data in format --> list[dict{str, str}]

'''
BANDS = [       
     {'id': 1, 'name': 'The Kinks', 'genre': 'Rock'},
     {'id': 2, 'name': 'Aphex Twin', 'genre': 'Electronic' },
         {'id': 3, 'name': 'Black Sabbath', 'genre': 'Metal', 'albums': [{'title': 'Master of Reality', 'release_date': '1971-07-21'}]},
     {'id': 4, 'name': 'Wu-Tang Clan', 'genre': 'Hip-Hop'},
]
'''
@app.get('/bands')
async def bands(genre: Optional[GenreURLChoices] = None, 
                q: Annotated[Optional[str], Query(max_length=10)] = None,
                has_albums: bool = False, session: Session = Depends(get_session)
                ) -> list[Band]:
    band_list = session.exec(select(Band)).all()   
    if genre:
        band_list = [b for b in band_list if b.genre.value.lower() == genre.value]
    if q:
        band_list = [b for b in band_list if q.lower() in b.name.lower()]    
    return band_list

@app.get('/bands/{band_id}') #ROUTE
async def band(band_id: int,
               session: Session = Depends(get_session)               
               ) -> Band:   
  band = session.get(Band, band_id)
  if band is None: 
    raise HTTPException(status_code = 404, detail = 'Band not found')
  return band
 
# @app.get('/bands/genre/{genre}')
# async def bands_for_genre(genre: GenreURLChoices) -> list[dict]:  #NOT USING PYDANTIC HERE
#     return[
#       b for b in BANDS if b['genre'].lower() == genre.value
#     ]


@app.post('/bands')
async def create_bands(
   band_data: BandCreate,
   session: Session = Depends(get_session)
   )-> Band:
   band = Band(name=band_data.name, genre=band_data.genre)
   session.add(band)

   if band_data.albums:
      for album in band_data.albums:
         album_obj = Album(title=album.title, release_date=album.release_date, band=band)
         session.add(album_obj)       

   session.commit()
   session.refresh(band)
   return band

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

@app.get('/views/rock_bands')
async def get_rock_bands(session: Session = Depends(get_session)):
    results = session.exec(text("SELECT * FROM rock_bands_view")).all()
    # Results is a list of tuples, map them to dictionary for JSON serialization
    return [{"id": r[0], "name": r[1], "genre": r[2], "date": r[3]} for r in results]

@app.get('/views/metal_bands')
async def get_metal_bands(session: Session = Depends(get_session)):
    results = session.exec(text("SELECT * FROM metal_bands_view")).all()
    return [{"id": r[0], "name": r[1], "genre": r[2], "date": r[3]} for r in results]

@app.get('/logs')
async def get_logs(session: Session = Depends(get_session)) -> list[AuditLog]:
    logs = session.exec(select(AuditLog).order_by(AuditLog.timestamp.desc())).all()
    return logs

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")