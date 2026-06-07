from sqlmodel import create_engine, SQLModel, Session, text

DATABASE_URL = 'sqlite:///db.sqlite'

engine = create_engine(DATABASE_URL, echo = True)

def init_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.exec(text("CREATE VIEW IF NOT EXISTS rock_bands_view AS SELECT * FROM band WHERE genre = 'Rock'"))
        session.exec(text("CREATE VIEW IF NOT EXISTS metal_bands_view AS SELECT * FROM band WHERE genre = 'Metal'"))
        session.exec(text('''
            CREATE TRIGGER IF NOT EXISTS band_delete_audit
            AFTER DELETE ON band
            BEGIN
                INSERT INTO auditlog (band_name, timestamp) VALUES (OLD.name, CURRENT_TIMESTAMP);
            END;
        '''))
        session.commit()
        
        # Seed initial data if empty
        from models import Band, Album
        from datetime import date
        if not session.exec(text("SELECT COUNT(*) FROM band")).first()[0]:
            kinks = Band(name='The Kinks', genre='Rock')
            aphex = Band(name='Aphex Twin', genre='Electronic')
            sabbath = Band(name='Black Sabbath', genre='Metal')
            session.add_all([kinks, aphex, sabbath])
            session.commit()
            
            # Add album for Black Sabbath
            master_of_reality = Album(title='Master of Reality', release_date=date(1971, 7, 21), band=sabbath)
            session.add(master_of_reality)
            
            wu = Band(name='Wu-Tang Clan', genre='Hip-Hop')
            session.add(wu)
            session.commit()
            
def get_session():
    with Session(engine) as session:
        yield session   