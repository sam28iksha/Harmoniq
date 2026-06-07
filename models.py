from typing import Optional
from enum import Enum
from pydantic import BaseModel, field_validator
from datetime import date
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime


class GenreURLChoices(str, Enum):    #TO SET ONLY POSSIBLE OPTIONS IN THE ROUTE
    ROCK = 'rock'
    ELECTRONIC = 'electronic'
    METAL = 'metal'
    HIP_HOP = 'hip-hop'

class GenreChoices(str, Enum):    #TO SET ONLY POSSIBLE OPTIONS IN THE ROUTE
    ROCK = 'Rock'
    ELECTRONIC = 'Electronic'
    METAL = 'Metal'
    HIP_HOP = 'Hip-Hop'


class AlbumBase(SQLModel):    #Inherits from SQLMODEL
    title: str
    release_date: date
    band_id : Optional[int] = Field(default=None, foreign_key="band.id")



class BandBase(SQLModel):        #PYDANTIC SCHEMA FOR BANDS
    name: str
    genre: GenreChoices
    

class BandCreate(BandBase):
    albums: Optional[list[AlbumBase]] = None
    @field_validator('genre', mode = 'before')
    def title_case_genre(cls, value):
        return value.title() #converts the string to title case

class BandUpdate(SQLModel):
    name: Optional[str] = None
    genre: Optional[GenreChoices] = None

    @field_validator('genre', mode='before')
    def title_case_genre(cls, value):
        if value:
            return value.title()
        return value


class Band(BandBase, table = True):
    id : int = Field(default = None, primary_key=True)
    albums: list["Album"] = Relationship(back_populates="band")
    date: Optional[date]

class Album(AlbumBase, table = True):
    id : int = Field(default=None, primary_key=True)
    band: Band = Relationship(back_populates="albums")

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    band_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)