# models.py

from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Integer, BigInteger, Text, JSON, Date, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # ✅ Changed to BigInteger
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    email_verified = Column(Boolean, default=False)
    device_id = Column(String, nullable=True)
    device_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Class(Base):
    __tablename__ = "classes"
    
    id = Column(BigInteger, primary_key=True)  # ✅ Changed to BigInteger
    teacher_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))  # ✅ Changed to BigInteger
    name = Column(String, nullable=False)
    class_id = Column(String, unique=True, nullable=True)
    enrollment_mode = Column(String, default="manual_entry")
    custom_columns = Column(JSON, default=list)
    thresholds = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class ClassStudent(Base):
    """Students in a class (for manual_entry and import_data modes)"""
    __tablename__ = "class_students"
    
    id = Column(BigInteger, primary_key=True)  # ✅ Changed to BigInteger
    class_id = Column(BigInteger, ForeignKey("classes.id", ondelete="CASCADE"))  # ✅ Changed to BigInteger
    student_id = Column(BigInteger, nullable=False)  # ✅ Changed to BigInteger
    name = Column(String, nullable=False)
    roll_no = Column(String, default="")
    attendance = Column(JSON, default=dict)
    custom_data = Column(JSON, default=dict)  # For custom columns
    created_at = Column(DateTime, default=datetime.utcnow)

class StudentUser(Base):
    """Student accounts (for enrollment_via_id mode)"""
    __tablename__ = "student_users"
    
    id = Column(BigInteger, primary_key=True)  # ✅ Changed to BigInteger
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))  # ✅ Changed to BigInteger
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    device_id = Column(String)
    device_info = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Enrollment(Base):
    """Student enrollments in classes"""
    __tablename__ = "enrollments"
    
    id = Column(BigInteger, primary_key=True)  # ✅ Changed to BigInteger
    student_user_id = Column(BigInteger, ForeignKey("student_users.id", ondelete="CASCADE"))  # ✅ Changed to BigInteger
    class_id = Column(BigInteger, ForeignKey("classes.id", ondelete="CASCADE"))  # ✅ Changed to BigInteger
    name = Column(String, nullable=False)
    roll_no = Column(String, default="")
    enrolled_at = Column(DateTime, default=datetime.utcnow)

class QRSession(Base):
    """Active QR attendance sessions"""
    __tablename__ = "qr_sessions"
    
    id = Column(BigInteger, primary_key=True)  # ✅ Changed to BigInteger
    class_id = Column(BigInteger, ForeignKey("classes.id", ondelete="CASCADE"))  # ✅ Changed to BigInteger
    teacher_id = Column(BigInteger, ForeignKey("users.id"))  # ✅ Changed to BigInteger
    date = Column(String, nullable=False)
    session_number = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    rotation_interval = Column(Integer, default=5)
    current_code = Column(String, nullable=False)
    code_generated_at = Column(DateTime, default=datetime.utcnow)
    scanned_students = Column(JSON, default=list)
    status = Column(String, default="active")

class VerificationCode(Base):
    __tablename__ = 'verification_codes'
    
    id = Column(BigInteger, primary_key=True, index=True)  # ✅ Changed to BigInteger
    email = Column(String, nullable=False)
    code = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    
    id = Column(BigInteger, primary_key=True)  # ✅ Changed to BigInteger
    class_id = Column(BigInteger, ForeignKey("classes.id"), nullable=False)  # ✅ Changed to BigInteger
    date = Column(Date, nullable=False)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
