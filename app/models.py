from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, Float, String, Boolean, Date,
    DateTime, Text, ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    sex = Column(String)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    goal = Column(String)
    activity_level = Column(String)
    dietary_restrictions = Column(Text, default="[]")
    injuries = Column(Text, default="[]")
    bmr = Column(Float, nullable=True)
    tdee = Column(Float, nullable=True)
    target_kcal = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meal_plans = relationship("MealPlan", back_populates="client", cascade="all, delete-orphan")
    workout_plans = relationship("WorkoutPlan", back_populates="client", cascade="all, delete-orphan")
    logs = relationship("DailyLog", back_populates="client", cascade="all, delete-orphan")


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    plan_data = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    client = relationship("Client", back_populates="meal_plans")


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    plan_data = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    client = relationship("Client", back_populates="workout_plans")


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    log_date = Column(Date, nullable=False)
    body_weight_kg = Column(Float, nullable=True)
    food_items = Column(Text, default="[]")
    total_kcal_consumed = Column(Float, default=0.0)
    total_protein_g = Column(Float, default=0.0)
    total_carbs_g = Column(Float, default=0.0)
    total_fat_g = Column(Float, default=0.0)
    workout_done = Column(Boolean, default=False)
    workout_notes = Column(Text, default="")
    general_notes = Column(Text, default="")
    kcal_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="logs")

    __table_args__ = (UniqueConstraint("client_id", "log_date", name="uq_client_log_date"),)
