from sqlmodel import create_engine, SQLModel, Session, text

DATABASE_URL = 'postgresql://harmoniq_user:harmoniq123@127.0.0.1:5432/harmoniq'

engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    """Initialize database: create tables, views, triggers, and stored procedures."""
    # Import models so SQLModel registers them before create_all
    from models import Band, Album, AuditLog  # noqa: F401
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # =============================================
        # VIEWS (2 Views)
        # =============================================

        # View 1: Rock bands view
        session.exec(text("""
            CREATE OR REPLACE VIEW rock_bands_view AS
            SELECT id, name, genre, date
            FROM band
            WHERE genre = 'ROCK';
        """))

        # View 2: Metal bands view
        session.exec(text("""
            CREATE OR REPLACE VIEW metal_bands_view AS
            SELECT id, name, genre, date
            FROM band
            WHERE genre = 'METAL';
        """))

        # =============================================
        # TRIGGERS (2 Triggers)
        # =============================================

        # Trigger Function 1: Log band deletions
        session.exec(text("""
            CREATE OR REPLACE FUNCTION log_band_deletion()
            RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO auditlog (band_name, action, timestamp)
                VALUES (OLD.name, 'DELETE', NOW());
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;
        """))

        session.exec(text("""
            DROP TRIGGER IF EXISTS band_delete_audit ON band;
        """))

        session.exec(text("""
            CREATE TRIGGER band_delete_audit
            AFTER DELETE ON band
            FOR EACH ROW
            EXECUTE FUNCTION log_band_deletion();
        """))

        # Trigger Function 2: Log band insertions
        session.exec(text("""
            CREATE OR REPLACE FUNCTION log_band_insertion()
            RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO auditlog (band_name, action, timestamp)
                VALUES (NEW.name, 'INSERT', NOW());
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))

        session.exec(text("""
            DROP TRIGGER IF EXISTS band_insert_audit ON band;
        """))

        session.exec(text("""
            CREATE TRIGGER band_insert_audit
            AFTER INSERT ON band
            FOR EACH ROW
            EXECUTE FUNCTION log_band_insertion();
        """))

        # =============================================
        # STORED PROCEDURES (2 Stored Procedures)
        # =============================================

        # Stored Procedure 1: Get bands by genre with album count
        session.exec(text("""
            CREATE OR REPLACE FUNCTION get_bands_by_genre(p_genre VARCHAR)
            RETURNS TABLE (
                band_id INTEGER,
                band_name VARCHAR,
                band_genre VARCHAR,
                album_count BIGINT
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT b.id, b.name, b.genre::VARCHAR, COUNT(a.id)
                FROM band b
                LEFT JOIN album a ON a.band_id = b.id
                WHERE b.genre::VARCHAR = p_genre
                GROUP BY b.id, b.name, b.genre;
            END;
            $$ LANGUAGE plpgsql;
        """))

        # Stored Procedure 2: Transfer all albums from one band to another
        session.exec(text("""
            CREATE OR REPLACE FUNCTION transfer_albums(
                p_from_band_id INTEGER,
                p_to_band_id INTEGER
            )
            RETURNS TABLE (
                transferred_count INTEGER,
                from_band_name VARCHAR,
                to_band_name VARCHAR
            ) AS $$
            DECLARE
                v_count INTEGER;
                v_from_name VARCHAR;
                v_to_name VARCHAR;
            BEGIN
                -- Validate source band exists
                SELECT name INTO v_from_name FROM band WHERE id = p_from_band_id;
                IF v_from_name IS NULL THEN
                    RAISE EXCEPTION 'Source band with id % not found', p_from_band_id;
                END IF;

                -- Validate target band exists
                SELECT name INTO v_to_name FROM band WHERE id = p_to_band_id;
                IF v_to_name IS NULL THEN
                    RAISE EXCEPTION 'Target band with id % not found', p_to_band_id;
                END IF;

                -- Count albums to transfer
                SELECT COUNT(*)::INTEGER INTO v_count
                FROM album WHERE band_id = p_from_band_id;

                -- Transfer albums
                UPDATE album
                SET band_id = p_to_band_id
                WHERE band_id = p_from_band_id;

                -- Return result
                transferred_count := v_count;
                from_band_name := v_from_name;
                to_band_name := v_to_name;
                RETURN NEXT;
            END;
            $$ LANGUAGE plpgsql;
        """))

        session.commit()

        # Seed initial data if empty
        from models import Band, Album
        from datetime import date
        result = session.exec(text("SELECT COUNT(*) FROM band")).first()
        if result[0] == 0:
            kinks = Band(name='The Kinks', genre='Rock')
            aphex = Band(name='Aphex Twin', genre='Electronic')
            sabbath = Band(name='Black Sabbath', genre='Metal')
            session.add_all([kinks, aphex, sabbath])
            session.commit()

            # Add albums for Black Sabbath
            master_of_reality = Album(title='Master of Reality', release_date=date(1971, 7, 21), band=sabbath)
            paranoid = Album(title='Paranoid', release_date=date(1970, 9, 18), band=sabbath)
            session.add_all([master_of_reality, paranoid])

            wu = Band(name='Wu-Tang Clan', genre='Hip-Hop')
            session.add(wu)
            session.commit()


def get_session():
    with Session(engine) as session:
        yield session
