import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from server.database.models import User, Classement, Niveau, Entite
from server.database.base import SessionLocal, Base, engine

def initialize_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create initial levels
        niveau1 = Niveau(
            nom="Débutant",
            lettres_acceptees="abcdefghijklmnopqrstuvwxyz",
            timer=60,
            difficulte="facile"
        )
        
        niveau2 = Niveau(
            nom="Intermédiaire",
            lettres_acceptees="abcdefghijklmnopqrstuvwxyz",
            timer=45,
            difficulte="moyen"
        )
        
        db.add_all([niveau1, niveau2])
        db.commit()
        
        # Create initial entities
        entite1 = Entite(
            nom="Monstre",
            mot_pour_vaincre="victoire",
            timer_avant_attaque=30,
            mortalite=0.5,
            niveau_id=1
        )
        
        entite2 = Entite(
            nom="Dragon",
            mot_pour_vaincre="bravery",
            timer_avant_attaque=20,
            mortalite=0.7,
            niveau_id=2
        )
        
        db.add_all([entite1, entite2])
        db.commit()
        
        # Create test users
        user1 = User(
            nom="Joueur1",
            niveau_actuel=1
        )
        
        user2 = User(
            nom="Joueur2",
            niveau_actuel=2
        )
        
        db.add_all([user1, user2])
        db.commit()
        
        # Create rankings
        classement1 = Classement(
            userID=1,
            place=1
        )
        
        classement2 = Classement(
            userID=2,
            place=2
        )
        
        db.add_all([classement1, classement2])
        db.commit()
        
        print("Database initialized with sample data")
        
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    initialize_database()
