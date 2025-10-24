from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, Date
from sqlalchemy.orm import relationship

Base = declarative_base()

class Otdel(Base):
    __tablename__ = 'otdel'
    otdel_id = Column(Integer, primary_key=True)
    name_otdel = Column(String, nullable=False)

class Post(Base):
    __tablename__ = 'post'
    post_id = Column(Integer, primary_key=True)
    name_post = Column(String, nullable=False)

class Role(Base):
    __tablename__ = 'role'
    role_id = Column(Integer, primary_key=True)
    name_role = Column(String, nullable=False)

class Employee(Base):
    __tablename__ = 'employee'
    employee_id = Column(Integer, primary_key=True)
    surname = Column(String, nullable=False)
    name = Column(String, nullable=False)
    patronymic = Column(String, nullable=False)
    login = Column(String, nullable=False)
    password = Column(String, nullable=False)
    idle_hours = Column(Integer, nullable=False)
    otdel_id = Column(Integer, ForeignKey('otdel.otdel_id'), nullable=False)
    post_id = Column(Integer, ForeignKey('post.post_id'), nullable=False)
    role_id = Column(Integer, ForeignKey('role.role_id'), nullable=False)

    otdel = relationship('Otdel')
    post = relationship('Post')
    role = relationship('Role')

class ActionType(Base):
    __tablename__ = 'actiontype'
    actiontype_id = Column(Integer, primary_key=True)
    name_type = Column(String, nullable=False)

class Action(Base):
    __tablename__ = 'action'
    action_id = Column(Integer, primary_key=True)
    hours = Column(Integer, nullable=False)
    date_action = Column(Date, nullable=False)
    employee_id = Column(Integer, ForeignKey('employee.employee_id'), nullable=False)
    actiontype_id = Column(Integer, ForeignKey('actiontype.actiontype_id'), nullable=False)

    employee = relationship('Employee')
    actiontype = relationship('ActionType')

