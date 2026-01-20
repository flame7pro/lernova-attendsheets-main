from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Date, ForeignKey, Text, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    classes = relationship("Class", back_populates="teacher", cascade="all, delete-orphan")
    qr_sessions = relationship("QRSession", back_populates="teacher", cascade="all, delete-orphan")

class StudentUser(Base):
    __tablename__ = "student_users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")

class Class(Base):
    __tablename__ = "classes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    teacher_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    teacher = relationship("User", back_populates="classes")
    enrollments = relationship("Enrollment", back_populates="class_obj", cascade="all, delete-orphan")
    qr_sessions = relationship("QRSession", back_populates="class_obj", cascade="all, delete-orphan")
    class_students = relationship("ClassStudent", back_populates="class_obj", cascade="all, delete-orphan")

class ClassStudent(Base):
    """Students in a class (for manual_entry and import_data modes)"""
    __tablename__ = "class_students"
    
    id = Column(BigInteger, primary_key=True, index=True)
    class_id = Column(BigInteger, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(BigInteger, nullable=False)
    name = Column(String, nullable=False)
    roll_no = Column(String, default="")
    attendance = Column(JSON, default=dict)
    custom_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    class_obj = relationship("Class", back_populates="class_students")

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(BigInteger, primary_key=True, index=True)
    student_user_id = Column(BigInteger, ForeignKey('student_users.id'), nullable=False)
    class_id = Column(BigInteger, ForeignKey('classes.id'), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    
    student = relationship("StudentUser", back_populates="enrollments")
    class_obj = relationship("Class", back_populates="enrollments")

class QRSession(Base):
    __tablename__ = "qr_sessions"
    
    id = Column(BigInteger, primary_key=True, index=True)
    teacher_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    class_id = Column(BigInteger, ForeignKey('classes.id'), nullable=False)
    qr_code = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    teacher = relationship("User", back_populates="qr_sessions")
    class_obj = relationship("Class", back_populates="qr_sessions")

class VerificationCode(Base):
    __tablename__ = "verification_codes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    
    id = Column(BigInteger, primary_key=True, index=True)
    class_id = Column(BigInteger, ForeignKey('classes.id'), nullable=False)
    date = Column(Date, nullable=False)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
