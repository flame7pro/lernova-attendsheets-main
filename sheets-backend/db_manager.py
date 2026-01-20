# db_manager.py - PostgreSQL Version

import os
import json
import random
import string
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from database import SessionLocal
from models import (
    User,
    Class,
    ClassStudent,
    StudentUser,
    Enrollment,
    QRSession,
    VerificationCode,
    AttendanceSession,
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

    def create_user(
        self,
        user_id: str,
        email: str,
        password_hash: str,
        name: str,
        role: str = "teacher",
        device_id: Optional[str] = None,
        device_info: Optional[Dict] = None,
    ) -> Dict[str, Any]:
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
                email_verified=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            return {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "email_verified": user.email_verified,
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
                "device_info": user.device_info,
            }
        finally:
            db.close()

    def is_trusted_device(self, userdata: Dict[str, Any], device_id: str) -> bool:
        """Check if device is trusted."""
        trusted_devices = userdata.get('trusted_devices', [])
        return any(d.get('id') == device_id for d in trusted_devices)

    def add_trusted_device(self, user_id: str, device_info: Dict[str, Any]) -> bool:
        """Add a trusted device for a user"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Initialize device_info if None
            if not user.device_info:
                user.device_info = {}
            
            # Get existing trusted_devices from device_info JSON
            trusted_devices = user.device_info.get('trusted_devices', [])
            device_id = device_info.get('id')
            
            # Check if device already exists
            device_exists = False
            for device in trusted_devices:
                if device.get('id') == device_id:
                    device['last_seen'] = datetime.utcnow().isoformat()
                    device['login_count'] = device.get('login_count', 0) + 1
                    device_exists = True
                    break
            
            if not device_exists:
                new_device = {
                    'id': device_id,
                    'name': device_info.get('name', 'Unknown Device'),
                    'browser': device_info.get('browser', 'Unknown'),
                    'os': device_info.get('os', 'Unknown'),
                    'device': device_info.get('device', 'Unknown'),
                    'first_seen': datetime.utcnow().isoformat(),
                    'last_seen': datetime.utcnow().isoformat(),
                    'login_count': 1
                }
                trusted_devices.append(new_device)
            
            # Update device_info with trusted_devices
            user.device_info['trusted_devices'] = trusted_devices
            
            # Mark modified for SQLAlchemy to detect JSON change
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(user, 'device_info')
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"Add trusted device error: {e}")
            db.rollback()
            return False
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
                "email_verified": user.email_verified,
            }
        finally:
            db.close()

    # Convenience wrapper expected by main.py
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.get_user_by_id(user_id)

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
        except Exception:
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
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    def update_user(self, user_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Update user name"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            user.name = name
            db.commit()
            db.refresh(user)

            return {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "email_verified": user.email_verified,
                "device_id": user.device_id,
                "device_info": user.device_info,
            }
        except Exception as e:
            db.rollback()
            print(f"Update user error: {e}")
            return None
        finally:
            db.close()

    # Used by main.py to update overview/name – same as update_user for now
    def update_user_overview(self, user_id: str, name: str) -> Optional[Dict[str, Any]]:
        return self.update_user(user_id, name)

    def update_student(
        self,
        student_id: str,
        name: str = None,
        device_id: str = None,
        device_info: dict = None,
    ):
        """Update student information (users table, role=student)"""
        db = self._get_db()
        try:
            student = (
                db.query(User)
                .filter(User.id == student_id, User.role == "student")
                .first()
            )

            if not student:
                return None

            if name:
                student.name = name
            if device_id:
                student.device_id = device_id
            if device_info:
                student.device_info = device_info

            db.commit()
            db.refresh(student)

            return {
                "id": student.id,
                "email": student.email,
                "name": student.name,
                "device_id": student.device_id,
                "device_info": student.device_info,
                "is_verified": student.email_verified,
                "role": student.role,
            }
        except Exception as e:
            print(f"Update student error: {e}")
            db.rollback()
            return None
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
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    # ==================== CLASS OPERATIONS ====================

    def create_class(self, teacher_id: str, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new class"""
        db = self._get_db()
        try:
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
                thresholds=class_data.get("thresholds", {}),
            )
            db.add(new_class)
            db.flush()

            if class_data.get("students"):
                for student_data in class_data["students"]:
                    student = ClassStudent(
                        class_id=new_class.id,
                        student_id=student_data["id"],
                        name=student_data["name"],
                        roll_no=student_data.get("rollNo", ""),
                        attendance=student_data.get("attendance", {}),
                        custom_data={
                            k: v
                            for k, v in student_data.items()
                            if k not in ["id", "name", "rollNo", "attendance"]
                        },
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

    def get_class_sessions(self, class_id: int, date_start: Optional[str] = None, date_end: Optional[str] = None,) -> List[Dict[str, Any]]:
        """Get all sessions for a class, optionally filtered by date range."""
        db = self._get_db()
        try:
            query = db.query(AttendanceSession).filter(
                AttendanceSession.class_id == str(class_id)
            )

            # Optional date filtering if main.py sends extra args
            if date_start:
                query = query.filter(AttendanceSession.date >= date_start)
            if date_end:
                query = query.filter(AttendanceSession.date <= date_end)

            sessions = query.order_by(AttendanceSession.date.desc()).all()

            return [
                {
                    "id": session.id,
                    "class_id": session.class_id,
                    "date": session.date.isoformat() if session.date else None,
                    "title": session.title,
                    "created_at": session.created_at.isoformat()
                    if session.created_at
                    else None,
                }
                for session in sessions
            ]
        except Exception as e:
            print(f"Get class sessions error: {e}")
            return []
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

    # Convenience wrapper expected by main.py
    def get_class(self, class_id: int) -> Optional[Dict[str, Any]]:
        return self.get_class_by_id(class_id)

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

            cls.name = class_data.get("name", cls.name)
            cls.custom_columns = class_data.get("customColumns", cls.custom_columns)
            cls.thresholds = class_data.get("thresholds", cls.thresholds)
            cls.enrollment_mode = class_data.get("enrollment_mode", cls.enrollment_mode)

            db.query(ClassStudent).filter(ClassStudent.class_id == class_id).delete()

            if class_data.get("students"):
                for student_data in class_data["students"]:
                    student = ClassStudent(
                        class_id=class_id,
                        student_id=student_data["id"],
                        name=student_data["name"],
                        roll_no=student_data.get("rollNo", ""),
                        attendance=student_data.get("attendance", {}),
                        custom_data={
                            k: v
                            for k, v in student_data.items()
                            if k not in ["id", "name", "rollNo", "attendance"]
                        },
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
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    def _generate_class_id(self) -> str:
        """Generate unique 8-character class ID"""
        db = self._get_db()
        try:
            while True:
                class_id = "".join(
                    random.choices(string.ascii_uppercase + string.digits, k=8)
                )
                existing = db.query(Class).filter(Class.class_id == class_id).first()
                if not existing:
                    return class_id
        finally:
            db.close()

    def _format_class(self, cls: Class, db: Session) -> Dict[str, Any]:
        """Format class object to dictionary"""
        students = db.query(ClassStudent).filter(ClassStudent.class_id == cls.id).all()

        students_list = []
        for student in students:
            student_dict = {
                "id": student.student_id,
                "name": student.name,
                "rollNo": student.roll_no,
                "attendance": student.attendance or {},
            }
            if student.custom_data:
                student_dict.update(student.custom_data)
            students_list.append(student_dict)

        return {
            "id": cls.id,
            "name": cls.name,
            "classId": cls.class_id,
            "enrollment_mode": cls.enrollment_mode,
            "customColumns": cls.custom_columns or [],
            "thresholds": cls.thresholds or [],
            "students": students_list,
        }

    # Placeholder for compatibility with old JSON-based code
    def get_class_file(self, user_id: str) -> str:
        return ""

    # ==================== STUDENT USER OPERATIONS ====================

    def create_student_user(
        self,
        student_id: str,
        user_id: str,
        name: str,
        email: str,
        device_id: Optional[str] = None,
        device_info: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create a student user account"""
        db = self._get_db()
        try:
            student = StudentUser(
                id=student_id,
                user_id=user_id,
                name=name,
                email=email,
                device_id=device_id,
                device_info=device_info,
            )
            db.add(student)
            db.commit()
            db.refresh(student)

            return {
                "id": student.id,
                "user_id": student.user_id,
                "name": student.name,
                "email": student.email,
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # Alias used by main.py
    def create_student(
        self,
        student_id: str,
        user_id: str,
        name: str,
        email: str,
        device_id: Optional[str] = None,
        device_info: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        return self.create_student_user(
            student_id, user_id, name, email, device_id, device_info
        )

    def get_student_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get student (in users table) by email where role='student'"""
        db = self._get_db()
        try:
            user = db.query(User).filter(
                User.email == email,
                User.role == "student",
            ).first()
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
                "device_info": user.device_info,
            }
        except Exception as e:
            print(f"Get student by email error: {e}")
            return None
        finally:
            db.close()

    def get_student(self, student_user_id: str) -> Optional[Dict[str, Any]]:
        """Get StudentUser by ID"""
        db = self._get_db()
        try:
            student = (
                db.query(StudentUser)
                .filter(StudentUser.id == student_user_id)
                .first()
            )
            if not student:
                return None
            return {
                "id": student.id,
                "user_id": student.user_id,
                "name": student.name,
                "email": student.email,
                "device_id": student.device_id,
                "device_info": student.device_info,
            }
        finally:
            db.close()

    def delete_student(self, student_user_id: str) -> bool:
        """Delete a student user and their enrollments"""
        db = self._get_db()
        try:
            student = (
                db.query(StudentUser)
                .filter(StudentUser.id == student_user_id)
                .first()
            )
            if not student:
                return False

            db.query(Enrollment).filter(
                Enrollment.student_user_id == student_user_id
            ).delete()
            db.delete(student)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    def enroll_student(
        self, student_user_id: str, class_id: int, name: str, roll_no: str
    ) -> Dict[str, Any]:
        """Enroll a student in a class"""
        db = self._get_db()
        try:
            existing = db.query(Enrollment).filter(
                and_(
                    Enrollment.student_user_id == student_user_id,
                    Enrollment.class_id == class_id,
                )
            ).first()

            if existing:
                raise ValueError("Student already enrolled in this class")

            enrollment = Enrollment(
                student_user_id=student_user_id,
                class_id=class_id,
                name=name,
                roll_no=roll_no,
            )
            db.add(enrollment)
            db.commit()
            db.refresh(enrollment)

            return {
                "id": enrollment.id,
                "student_user_id": enrollment.student_user_id,
                "class_id": enrollment.class_id,
                "name": enrollment.name,
                "roll_no": enrollment.roll_no,
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def unenroll_student(self, student_user_id: str, class_id: int) -> bool:
        """Remove a student from a class"""
        db = self._get_db()
        try:
            db.query(Enrollment).filter(
                and_(
                    Enrollment.student_user_id == student_user_id,
                    Enrollment.class_id == class_id,
                )
            ).delete()
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    def get_student_enrollments(self, student_user_id: str) -> List[Dict[str, Any]]:
        """Get all enrollments for a student"""
        db = self._get_db()
        try:
            enrollments = db.query(Enrollment).filter(
                Enrollment.student_user_id == student_user_id
            ).all()

            result: List[Dict[str, Any]] = []
            for enrollment in enrollments:
                cls = db.query(Class).filter(Class.id == enrollment.class_id).first()
                if cls:
                    teacher = (
                        db.query(User).filter(User.id == cls.teacher_id).first()
                    )
                    result.append(
                        {
                            "classid": str(cls.id),
                            "classname": cls.name,
                            "teachername": teacher.name if teacher else "Unknown",
                            "roll_no": enrollment.roll_no,
                        }
                    )
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

            return [
                {
                    "id": e.id,
                    "student_user_id": e.student_user_id,
                    "name": e.name,
                    "roll_no": e.roll_no,
                    "enrolled_at": e.enrolled_at.isoformat()
                    if e.enrolled_at
                    else None,
                }
                for e in enrollments
            ]
        finally:
            db.close()

    def get_student_class_details(
        self, student_user_id: str, class_id: int
    ) -> Optional[Dict[str, Any]]:
        """Basic details about a student's enrollment in a class"""
        db = self._get_db()
        try:
            enrollment = db.query(Enrollment).filter(
                and_(
                    Enrollment.student_user_id == student_user_id,
                    Enrollment.class_id == class_id,
                )
            ).first()
            if not enrollment:
                return None

            cls = db.query(Class).filter(Class.id == class_id).first()
            teacher = db.query(User).filter(User.id == cls.teacher_id).first() if cls else None

            return {
                "class_id": class_id,
                "class_name": cls.name if cls else None,
                "teacher_name": teacher.name if teacher else None,
                "roll_no": enrollment.roll_no,
            }
        finally:
            db.close()

    def get_student_stats(
        self,
        student_user_id: str,
        class_id: int,
        date_start: str,
        date_end: str,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Stub: student attendance statistics per class (to be implemented properly)."""
        return {
            "total_classes": 0,
            "present": 0,
            "absent": 0,
            "late": 0,
            "percentage": 0.0,
            "status": "good",
        }

    # Used by main.py – simple stub for now
    def get_student_day_attendance(
        self, student_user_id: str, day: str
    ) -> List[Dict[str, Any]]:
        """Stub: per-day attendance entries for a student."""
        return []

    # ==================== QR CODE SYSTEM ====================

    def _generate_qr_code(self) -> str:
        """Generate random 8-character QR code"""
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def start_qr_session(
        self, class_id: int, teacher_id: str, date: str, rotation_interval: int = 5
    ) -> Dict[str, Any]:
        """Start QR attendance session"""
        db = self._get_db()
        try:
            existing = db.query(QRSession).filter(
                and_(
                    QRSession.class_id == class_id,
                    QRSession.date == date,
                    QRSession.status == "active",
                )
            ).first()

            if existing:
                raise ValueError("Active QR session already exists for this date")

            session_count = db.query(func.count(QRSession.id)).filter(
                and_(QRSession.class_id == class_id, QRSession.date == date)
            ).scalar() or 0

            qr_session = QRSession(
                class_id=class_id,
                teacher_id=teacher_id,
                date=date,
                session_number=session_count + 1,
                rotation_interval=rotation_interval,
                current_code=self._generate_qr_code(),
                status="active",
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
                "status": qr_session.status,
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
                    QRSession.status == "active",
                )
            ).first()

            if not session:
                return None

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
                "status": session.status,
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
                    QRSession.status == "active",
                )
            ).first()

            if not session:
                return False

            session.status = "completed"
            db.commit()
            return True
        except Exception:
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
                    QRSession.status == "active",
                )
            ).first()

            if not session:
                raise ValueError("No active QR session found")

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

    # Wrapper name likely used in main.py
    def scan_qr_code(self, class_id: int, date: str, student_user_id: str) -> bool:
        return self.mark_qr_attendance(class_id, date, student_user_id)

    # ==================== ATTENDANCE SESSION (non‑QR) ====================

    def create_attendance_session(
        self, class_id: int, session_date: str, session_name: str
    ) -> Dict[str, Any]:
        """Create a manual attendance session (non‑QR)."""
        db = self._get_db()
        try:
            session = AttendanceSession(
                id=str(int(datetime.utcnow().timestamp() * 1000)),
                class_id=str(class_id),
                date=datetime.fromisoformat(session_date).date(),
                title=session_name,
                created_at=datetime.utcnow(),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return {
                "id": session.id,
                "class_id": session.class_id,
                "date": session.date.isoformat(),
                "title": session.title,
                "created_at": session.created_at.isoformat(),
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def update_session_attendance(
        self, session_id: str, student_id: str, status: str
    ) -> bool:
        """Stub: Update attendance for a student in a session (to be implemented)."""
        # TODO: connect to an Attendance model/table if you add one.
        return True

    def delete_attendance_session(self, session_id: str) -> bool:
        db = self._get_db()
        try:
            session = (
                db.query(AttendanceSession)
                .filter(AttendanceSession.id == session_id)
                .first()
            )
            if not session:
                return False
            db.delete(session)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    # ==================== VERIFICATION CODE OPERATIONS ====================

    def save_verification_code(
        self, email: str, code: str, purpose: str, expires_at: datetime, extra_data: Dict = None
    ) -> bool:
        """Save verification code with optional extra data"""
        db = self._get_db()
        try:
            # Delete old codes
            db.query(VerificationCode).filter(
                and_(
                    VerificationCode.email == email,
                    VerificationCode.purpose == purpose,
                )
            ).delete()
            
            verification = VerificationCode(
                email=email,
                code=code,
                purpose=purpose,
                expires_at=expires_at,
                extra_data=extra_data or {}  # ADD THIS
            )
            db.add(verification)
            db.commit()
            return True
        except Exception as e:
            print(f"Save verification error: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_verification_code(
        self, email: str, purpose: str
    ) -> Optional[Dict[str, Any]]:
        """Get verification code with extra_data"""
        db = self._get_db()
        try:
            code = db.query(VerificationCode).filter(
                and_(
                    VerificationCode.email == email,
                    VerificationCode.purpose == purpose,
                    VerificationCode.expires_at > datetime.utcnow(),
                )
            ).first()
            
            if not code:
                return None
            
            result = {
                "email": code.email,
                "code": code.code,
                "purpose": code.purpose,
                "expires_at": code.expires_at.isoformat(),
            }
            
            # Merge extra_data (password_hash, name, role, device_info)
            if hasattr(code, 'extra_data') and code.extra_data:
                result.update(code.extra_data)
            
            return result
        finally:
            db.close()

    def delete_verification_code(self, email: str, purpose: str) -> bool:
        """Delete verification code"""
        db = self._get_db()
        try:
            db.query(VerificationCode).filter(
                and_(
                    VerificationCode.email == email,
                    VerificationCode.purpose == purpose,
                )
            ).delete()
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    # ==================== CONTACT OPERATIONS ====================

    def save_contact_message(self, email: str, message_data: Dict[str, Any]) -> bool:
        """Save contact form message - stored in logs for now"""
        print(f"[CONTACT] Message from {email}: {message_data}")
        return True

    def get_contact_messages(self, email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get contact messages (not persisted yet)"""
        return []

    # ==================== STATS / ANALYTICS (stubs) ====================

    def calculate_class_statistics(
        self,
        teacher_id: str,
        class_id: int,
        date_start: str,
        date_end: str,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Stub: high-level stats for a class."""
        return {
            "total_classes": 0,
            "total_students": 0,
            "avg_attendance": 0.0,
            "excellent": 0,
            "at_risk": 0,
        }

    def get_class_day_stats(
        self,
        teacher_id: str,
        class_id: int,
        day: str,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Stub: per-day class stats."""
        return {
            "date": day,
            "present": 0,
            "absent": 0,
            "late": 0,
            "percentage": 0.0,
        }

    def get_student_day_stats(
        self,
        student_user_id: str,
        day: str,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Stub: per-day student stats."""
        return {
            "date": day,
            "classes": 0,
            "present": 0,
            "absent": 0,
            "late": 0,
            "percentage": 0.0,
            "status": "good",
        }

    def get_student_month_stats(
        self,
        student_user_id: str,
        year: int,
        month: int,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Stub: per-month student stats."""
        return {
            "year": year,
            "month": month,
            "total_classes": 0,
            "present": 0,
            "absent": 0,
            "late": 0,
            "percentage": 0.0,
            "status": "good",
        }

    # ==================== COMPATIBILITY HELPERS ====================

    def read_json(self, file_path: str) -> Optional[Dict]:
        return None

    def write_json(self, file_path: str, data: Dict) -> bool:
        return True

    def get_user_dir(self, user_id: str) -> str:
        return ""

    def get_classes_file(self, user_id: str) -> str:
        return ""

    def get_qr_sessions_dir(self) -> str:
        return ""

    def ensure_qr_sessions_dir(self):
        pass

    def get_qr_session_file(self, class_id: str, date: str) -> str:
        return ""

    def backup_user_data(self, user_id: str, backup_dir: str = "backups"):
        pass

    # ==================== DB STATS ====================

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
                "timestamp": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()
