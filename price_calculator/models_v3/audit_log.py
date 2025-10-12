"""
AuditLog Model - История изменений (для будущего логирования)
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .base import Base


class AuditLog(Base):
    """
    Журнал аудита изменений
    
    ВНИМАНИЕ: Таблица создаётся, но пока НЕ используется.
    В будущем здесь будет логироваться вся история изменений позиций,
    расчётов и маршрутов для отслеживания изменений цен и условий.
    """
    
    __tablename__ = 'v3_audit_logs'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Информация о сущности
    entity_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Тип сущности: Position, Calculation, LogisticsRoute, Factory"
    )
    entity_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="ID изменённой сущности"
    )
    
    # Информация о пользователе (для будущего)
    user_id = Column(
        Integer,
        index=True,
        comment="ID пользователя (когда будет система пользователей)"
    )
    
    # Действие
    action = Column(
        String(20),
        nullable=False,
        comment="Тип действия: created, updated, deleted"
    )
    
    # Изменения
    changes = Column(
        JSONB,
        comment="JSON с изменениями: {'field': {'old': ..., 'new': ...}}"
    )
    
    # Метаданные
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, entity={self.entity_type}:{self.entity_id}, action={self.action})>"
    
    def to_dict(self):
        """Сериализация для API"""
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'user_id': self.user_id,
            'action': self.action,
            'changes': self.changes or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }



