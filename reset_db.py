from app import app, db

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(db.text('DROP TABLE IF EXISTS session CASCADE;'))
        conn.execute(db.text('DROP TABLE IF EXISTS "user" CASCADE;'))
        db.create_all()
