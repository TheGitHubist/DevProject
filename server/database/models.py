from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(50), nullable=False)
    niveau_actuel = Column(Integer, ForeignKey('niveaux.id'))
    
    classement = relationship("Classement", back_populates="user")
    niveau = relationship("Niveau", foreign_keys=[niveau_actuel])

class Classement(Base):
    __tablename__ = 'classements'
    
    id = Column(Integer, primary_key=True)
    userID = Column(Integer, ForeignKey('users.id'))
    place = Column(Integer)
    
    user = relationship("User", back_populates="classement")

class Niveau(Base):
    __tablename__ = 'niveaux'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    lettres_acceptees = Column(String(50))
    timer = Column(Integer)
    difficulte = Column(String(20))
    
    entites = relationship("Entite", back_populates="niveau")

class Entite(Base):
    __tablename__ = 'entites'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(50), nullable=False)
    mot_pour_vaincre = Column(String(50))
    timer_avant_attaque = Column(Integer)
    mortalite = Column(Float)
    niveau_id = Column(Integer, ForeignKey('niveaux.id'))
    
    niveau = relationship("Niveau", back_populates="entites")
