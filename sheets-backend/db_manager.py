# db_manager.py - PostgreSQL Version (PART 1 of 3)
import os
import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from database import SessionLocal
from models import (
    User, Class, ClassStudent, StudentUser, 
    Enrollment, QRSession, VerificationCode
)

class DatabaseManager:
    def __init__(self, base_dir: str = "data"):
        """Initialize DatabaseManager with PostgreSQL"""
        self.base_dir = base_dir
        
    def _get_db(self) -> Session:
        """Helper to get database session"""
        return SessionLocal()

    # ==================== USER OPERATIONS ====================
    
    def user_exists(self, email: str) -> bool:
        """Check if user exists by email"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.email == email).first()
            return user is not None
        finally:
            db.close()
    
    def create_user(self, user_id: str, email: str, password_hash: str, 
                   name: str, role: str = "teacher", 
                   device_id: Optional[str] = None, 
                   device_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new user"""
        db = self._get_db()
        try:
            user = User(
                id=user_id,
                email=email,
                password_hash=password_hash,
                name=name,
                role=role,
                device_id=device_id,
                device_info=device_info,
                email_verified=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "email_verified": user.email_verified
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            return {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "password_hash": user.password_hash,
                "role": user.role,
                "email_verified": user.email_verified,
                "device_id": user.device_id,
                "device_info": user.device_info
            }
        finally:
            db.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            return {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "email_verified": user.email_verified
            }
        finally:
            db.close()
    
    def update_user_verification(self, email: str, verified: bool = True) -> bool:
        """Update user email verification status"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return False
            user.email_verified = verified
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()
    
    def update_user_password(self, email: str, new_password_hash: str) -> bool:
        """Update user password"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return False
            user.password_hash = new_password_hash
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()
    
    def update_user_name(self, user_id: str, new_name: str) -> bool:
        """Update user name"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            user.name = new_name
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user and all associated data"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            db.delete(user)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()

    # ==================== CLASS OPERATIONS ====================
    
    def create_class(self, teacher_id: str, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new class"""
        db = self._get_db()
        try:
            # Generate class_id if enrollment_via_id mode
            class_id_str = None
            if class_data.get("enrollment_mode") == "enrollment_via_id":
                class_id_str = self._generate_class_id()
            
            new_class = Class(
                id=class_data["id"],
                teacher_id=teacher_id,
                name=class_data["name"],
                class_id=class_id_str,
                enrollment_mode=class_data.get("enrollment_mode", "manual_entry"),
                custom_columns=class_data.get("customColumns", []),
                thresholds=class_data.get("thresholds", {})
            )
            db.add(new_class)
            db.flush()
            
            # Add students if in manual_entry or import_data mode
            if class_data.get("students"):
                for student_data in class_data["students"]:
                    student = ClassStudent(
                        class_id=new_class.id,
                        student_id=student_data["id"],
                        name=student_data["name"],
                        roll_no=student_data.get("rollNo", ""),
                        attendance=student_data.get("attendance", {}),
                        custom_data={k: v for k, v in student_data.items() 
                                    if k not in ["id", "name", "rollNo", "attendance"]}
                    )
                    db.add(student)
            
            db.commit()
            db.refresh(new_class)
            
            return self._format_class(new_class, db)
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_all_classes(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Get all classes for a teacher"""
        db = self._get_db()
        try:
            classes = db.query(Class).filter(Class.teacher_id == teacher_id).all()
            return [self._format_class(cls, db) for cls in classes]
        finally:
            db.close()
    
    def get_class_by_id(self, class_id: int) -> Optional[Dict[str, Any]]:
        """Get class by ID"""
        db = self._get_db()
        try:
            cls = db.query(Class).filter(Class.id == class_id).first()
            if not cls:
                return None
            return self._format_class(cls, db)
        finally:
            db.close()
    
    def get_class_by_class_id(self, class_id: str) -> Optional[Dict[str, Any]]:
        """Get class by class_id string (for student enrollment)"""
        db = self._get_db()
        try:
            cls = db.query(Class).filter(Class.class_id == class_id).first()
            if not cls:
                return None
            return self._format_class(cls, db)
        finally:
            db.close()
    
    def update_class(self, class_id: int, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing class"""
        db = self._get_db()
        try:
            cls = db.query(Class).filter(Class.id == class_id).first()
            if not cls:
                raise ValueError(f"Class {class_id} not found")
            
            # Update class fields
            cls.name = class_data.get("name", cls.name)
            cls.custom_columns = class_data.get("customColumns", cls.custom_columns)
            cls.thresholds = class_data.get("thresholds", cls.thresholds)
            cls.enrollment_mode = class_data.get("enrollment_mode", cls.enrollment_mode)
            
            # Delete existing students and recreate
            db.query(ClassStudent).filter(ClassStudent.class_id == class_id).delete()
            
            # Add updated students
            if class_data.get("students"):
                for student_data in class_data["students"]:
                    student = ClassStudent(
                        class_id=class_id,
                        student_id=student_data["id"],
                        name=student_data["name"],
                        roll_no=student_data.get("rollNo", ""),
                        attendance=student_data.get("attendance", {}),
                        custom_data={k: v for k, v in student_data.items() 
                                    if k not in ["id", "name", "rollNo", "attendance"]}
                    )
                    db.add(student)
            
            db.commit()
            db.refresh(cls)
            
            return self._format_class(cls, db)
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def delete_class(self, class_id: int) -> bool:
        """Delete a class"""
        db = self._get_db()
        try:
            cls = db.query(Class).filter(Class.id == class_id).first()
            if not cls:
                return False
            db.delete(cls)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()
    
    def _generate_class_id(self) -> str:
        """Generate unique 8-character class ID"""
        db = self._get_db()
        try:
            while True:
                class_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                existing = db.query(Class).filter(Class.class_id == class_id).first()
                if not existing:
                    return class_id
        finally:
            db.close()
    
    def _format_class(self, cls: Class, db: Session) -> Dict[str, Any]:
        """Format class object to dictionary"""
        # Get students for this class
        students = db.query(ClassStudent).filter(ClassStudent.class_id == cls.id).all()
        
        students_list = []
        for student in students:
            student_dict = {
                "id": student.student_id,
                "name": student.name,
                "rollNo": student.roll_no,
                "attendance": student.attendance or {}
            }
            # Add custom column data
            if student.custom_data:
                student_dict.update(student.custom_data)
            students_list.append(student_dict)
        
        return {
            "id": cls.id,
            "name": cls.name,
            "classId": cls.class_id,
            "enrollment_mode": cls.enrollment_mode,
            "customColumns": cls.custom_columns or [],
            "thresholds": cls.thresholds or {},
            "students": students_list
        }

    # ==================== STUDENT USER OPERATIONS ====================
    
    def create_student_user(self, student_id: str, user_id: str, name: str, email: str,
                           device_id: Optional[str] = None, device_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a student user account"""
        db = self._get_db()
        try:
            student = StudentUser(
                id=student_id,
                user_id=user_id,
                name=name,
                email=email,
                device_id=device_id,
                device_info=device_info
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            
            return {
                "id": student.id,
                "user_id": student.user_id,
                "name": student.name,
                "email": student.email
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_student_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get student by user_id"""
        db = self._get_db()
        try:
            student = db.query(StudentUser).filter(StudentUser.user_id == user_id).first()
            if not student:
                return None
            return {
                "id": student.id,
                "user_id": student.user_id,
                "name": student.name,
                "email": student.email,
                "device_id": student.device_id,
                "device_info": student.device_info
            }
        finally:
            db.close()
    
    def enroll_student(self, student_user_id: str, class_id: int, name: str, roll_no: str) -> Dict[str, Any]:
        """Enroll a student in a class"""
        db = self._get_db()
        try:
            # Check if already enrolled
            existing = db.query(Enrollment).filter(
                and_(
                    Enrollment.student_user_id == student_user_id,
                    Enrollment.class_id == class_id
                )
            ).first()
            
            if existing:
                raise ValueError("Student already enrolled in this class")
            
            enrollment = Enrollment(
                student_user_id=student_user_id,
                class_id=class_id,
                name=name,
                roll_no=roll_no
            )
            db.add(enrollment)
            db.commit()
            db.refresh(enrollment)
            
            return {
                "id": enrollment.id,
                "student_user_id": enrollment.student_user_id,
                "class_id": enrollment.class_id,
                "name": enrollment.name,
                "roll_no": enrollment.roll_no
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_student_enrollments(self, student_user_id: str) -> List[Dict[str, Any]]:
        """Get all enrollments for a student"""
        db = self._get_db()
        try:
            enrollments = db.query(Enrollment).filter(
                Enrollment.student_user_id == student_user_id
            ).all()
            
            result = []
            for enrollment in enrollments:
                cls = db.query(Class).filter(Class.id == enrollment.class_id).first()
                if cls:
                    teacher = db.query(User).filter(User.id == cls.teacher_id).first()
                    result.append({
                        "classid": str(cls.id),
                        "classname": cls.name,
                        "teachername": teacher.name if teacher else "Unknown",
                        "roll_no": enrollment.roll_no
                    })
            
            return result
        finally:
            db.close()
    
    def get_enrolled_students(self, class_id: int) -> List[Dict[str, Any]]:
        """Get all enrolled students for a class"""
        db = self._get_db()
        try:
            enrollments = db.query(Enrollment).filter(
                Enrollment.class_id == class_id
            ).all()
            
            return [{
                "id": e.id,
                "student_user_id": e.student_user_id,
                "name": e.name,
                "roll_no": e.roll_no,
                "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None
            } for e in enrollments]
        finally:
            db.close()

    def get_student_stats(self, student_user_id: str, class_id: int, date_start: str, date_end: str,
                         thresholds: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Calculate student attendance statistics"""
        return {
            "total_classes": 0,
            "present": 0,
            "absent": 0,
            "late": 0,
            "percentage": 0.0,
            "status": "good"
        }

    # ==================== QR CODE SYSTEM ====================
    
    def _generate_qr_code(self) -> str:
        """Generate random 8-character QR code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def start_qr_session(self, class_id: int, teacher_id: str, date: str, rotation_interval: int = 5) -> Dict[str, Any]:
        """Start QR attendance session"""
        db = self._get_db()
        try:
            # Check for existing active session
            existing = db.query(QRSession).filter(
                and_(
                    QRSession.class_id == class_id,
                    QRSession.date == date,
                    QRSession.status == "active"
                )
            ).first()
            
            if existing:
                raise ValueError("Active QR session already exists for this date")
            
            # Count existing sessions for this date
            session_count = db.query(func.count(QRSession.id)).filter(
                and_(
                    QRSession.class_id == class_id,
                    QRSession.date == date
                )
            ).scalar() or 0
            
            qr_session = QRSession(
                class_id=class_id,
                teacher_id=teacher_id,
                date=date,
                session_number=session_count + 1,
                rotation_interval=rotation_interval,
                current_code=self._generate_qr_code(),
                status="active"
            )
            db.add(qr_session)
            db.commit()
            db.refresh(qr_session)
            
            return {
                "class_id": qr_session.class_id,
                "teacher_id": qr_session.teacher_id,
                "date": qr_session.date,
                "session_number": qr_session.session_number,
                "started_at": qr_session.started_at.isoformat(),
                "rotation_interval": qr_session.rotation_interval,
                "current_code": qr_session.current_code,
                "code_generated_at": qr_session.code_generated_at.isoformat(),
                "scanned_students": qr_session.scanned_students or [],
                "status": qr_session.status
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_qr_session(self, class_id: int, date: str) -> Optional[Dict[str, Any]]:
        """Get active QR session"""
        db = self._get_db()
        try:
            session = db.query(QRSession).filter(
                and_(
                    QRSession.class_id == class_id,
                    QRSession.date == date,
                    QRSession.status == "active"
                )
            ).first()
            
            if not session:
                return None
            
            # Auto-rotate code if needed
            elapsed = (datetime.utcnow() - session.code_generated_at).total_seconds()
            if elapsed >= session.rotation_interval:
                session.current_code = self._generate_qr_code()
                session.code_generated_at = datetime.utcnow()
                db.commit()
            
            return {
                "class_id": session.class_id,
                "teacher_id": session.teacher_id,
                "date": session.date,
                "session_number": session.session_number,
                "started_at": session.started_at.isoformat(),
                "rotation_interval": session.rotation_interval,
                "current_code": session.current_code,
                "code_generated_at": session.code_generated_at.isoformat(),
                "scanned_students": session.scanned_students or [],
                "status": session.status
            }
        finally:
            db.close()
    
    def stop_qr_session(self, class_id: int, date: str) -> bool:
        """Stop active QR session"""
        db = self._get_db()
        try:
            session = db.query(QRSession).filter(
                and_(
                    QRSession.class_id == class_id,
                    QRSession.date == date,
                    QRSession.status == "active"
                )
            ).first()
            
            if not session:
                return False
            
            session.status = "completed"
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()
    
    def mark_qr_attendance(self, class_id: int, date: str, student_user_id: str) -> bool:
        """Mark attendance via QR scan"""
        db = self._get_db()
        try:
            session = db.query(QRSession).filter(
                and_(
                    QRSession.class_id == class_id,
                    QRSession.date == date,
                    QRSession.status == "active"
                )
            ).first()
            
            if not session:
                raise ValueError("No active QR session found")
            
            # Add student to scanned list
            scanned = session.scanned_students or []
            if student_user_id not in scanned:
                scanned.append(student_user_id)
                session.scanned_students = scanned
                db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # ==================== VERIFICATION CODE OPERATIONS ====================
    
    def save_verification_code(self, email: str, code: str, purpose: str, expires_at: datetime) -> bool:
        """Save verification code"""
        db = self._get_db()
        try:
            # Delete existing codes for this email and purpose
            db.query(VerificationCode).filter(
                and_(
                    VerificationCode.email == email,
                    VerificationCode.purpose == purpose
                )
            ).delete()
            
            verification = VerificationCode(
                email=email,
                code=code,
                purpose=purpose,
                expires_at=expires_at
            )
            db.add(verification)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_verification_code(self, email: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Get verification code"""
        db = self._get_db()
        try:
            code = db.query(VerificationCode).filter(
                and_(
                    VerificationCode.email == email,
                    VerificationCode.purpose == purpose,
                    VerificationCode.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not code:
                return None
            
            return {
                "email": code.email,
                "code": code.code,
                "purpose": code.purpose,
                "expires_at": code.expires_at.isoformat()
            }
        finally:
            db.close()
    
    def delete_verification_code(self, email: str, purpose: str) -> bool:
        """Delete verification code"""
        db = self._get_db()
        try:
            db.query(VerificationCode).filter(
                and_(
                    VerificationCode.email == email,
                    VerificationCode.purpose == purpose
                )
            ).delete()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()

    # ==================== CONTACT OPERATIONS ====================
    
    def save_contact_message(self, email: str, message_data: Dict[str, Any]) -> bool:
        """Save contact form message - stored in app logs for now"""
        print(f"[CONTACT] Message from {email}: {message_data}")
        return True
    
    def get_contact_messages(self, email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get contact messages"""
        return []

    # ==================== HELPER METHODS (kept for compatibility) ====================
    
    def read_json(self, file_path: str) -> Optional[Dict]:
        """Deprecated: kept for compatibility"""
        return None
    
    def write_json(self, file_path: str, data: Dict) -> bool:
        """Deprecated: kept for compatibility"""
        return True
    
    def get_user_dir(self, user_id: str) -> str:
        """Deprecated: kept for compatibility"""
        return ""
    
    def get_classes_file(self, user_id: str) -> str:
        """Deprecated: kept for compatibility"""
        return ""
    
    def get_qr_sessions_dir(self) -> str:
        """Deprecated: kept for compatibility"""
        return ""
    
    def ensure_qr_sessions_dir(self):
        """Deprecated: kept for compatibility"""
        pass
    
    def get_qr_session_file(self, class_id: str, date: str) -> str:
        """Deprecated: kept for compatibility"""
        return ""
    
    def backup_user_data(self, user_id: str, backup_dir: str = "backups"):
        """Deprecated: kept for compatibility"""
        pass
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        db = self._get_db()
        try:
            total_users = db.query(func.count(User.id)).scalar() or 0
            total_classes = db.query(func.count(Class.id)).scalar() or 0
            total_students = db.query(func.count(StudentUser.id)).scalar() or 0
            
            return {
                "total_users": total_users,
                "total_classes": total_classes,
                "total_students": total_students,
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            db.close()
