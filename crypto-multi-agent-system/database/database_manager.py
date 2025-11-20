"""
Database Manager для сохранения и анализа результатов
Первая версия - базовая структура
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from database.config import SessionLocal, engine
from database.models import (
    AnalysisSession, Token, TokenAnalysis, 
    Alert, TokenPerformance, SystemMetrics
)


class DatabaseManager:
    """Управляет сохранением и анализом результатов работы системы."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("DatabaseManager инициализирован")
    
    @contextmanager
    def get_session(self):
        """Контекстный менеджер для безопасной работы с БД."""
        db = SessionLocal()
        try:
            yield db
        except Exception as e:
            db.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            db.close()
    
    def test_connection(self) -> bool:
        """Тестовая проверка соединения с БД."""
        try:
            with self.get_session() as db:
                # Простой запрос с text()
                db.execute(text("SELECT 1"))
                self.logger.info("✅ Database connection OK")
                return True
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def create_analysis_session(self, cycle_number: int) -> int:
        """Создает новую сессию анализа и возвращает её ID."""
        try:
            with self.get_session() as db:
                session = AnalysisSession(
                    cycle_number=cycle_number,
                    timestamp=datetime.utcnow()
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                
                self.logger.info(f"✅ Создана сессия анализа ID={session.id}, cycle={cycle_number}")
                return session.id
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Ошибка создания сессии: {e}")
            return -1
    
    def save_or_update_token(self, token_data: Dict[str, Any]) -> bool:
        """Сохраняет или обновляет информацию о токене."""
        try:
            with self.get_session() as db:
                # Проверяем, существует ли токен
                existing_token = db.query(Token).filter_by(
                    token_address=token_data['token_address']
                ).first()
                
                if existing_token:
                    # Обновляем существующий
                    existing_token.last_seen_at = datetime.utcnow()
                    existing_token.discovery_count += 1
                    self.logger.debug(f"Обновлен токен {token_data['symbol']}")
                else:
                    # Создаем новый
                    new_token = Token(
                        token_address=token_data['token_address'],
                        symbol=token_data['symbol'],
                        name=token_data.get('name', ''),
                        chain_id=token_data['chain_id'],
                        dex=token_data.get('dex', ''),
                        pair_address=token_data.get('pair_address', '')
                    )
                    db.add(new_token)
                    self.logger.debug(f"Создан новый токен {token_data['symbol']}")
                
                db.commit()
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Ошибка сохранения токена: {e}")
            return False
    
    def save_token_analysis(self, session_id: int, token_data: Dict[str, Any], 
                           analysis_result: Dict[str, Any]) -> int:
        """Сохраняет результат анализа токена. Возвращает analysis_id."""
        try:
            with self.get_session() as db:
                # Сначала сохраняем/обновляем токен
                token_address = token_data['token_address']
                
                # Создаем запись анализа
                analysis = TokenAnalysis(
                    token_address=token_address,
                    session_id=session_id,
                    timestamp=datetime.utcnow(),
                    
                    # Основные данные
                    discovery_score=analysis_result.get('discovery_score', 0),
                    final_score=analysis_result.get('final_score', 0),
                    recommendation=analysis_result.get('recommendation', 'NO_POTENTIAL'),
                    
                    # Рыночные данные
                    price_usd=token_data.get('price_usd'),
                    liquidity_usd=token_data.get('liquidity_usd'),
                    volume_h24=token_data.get('volume_h24'),
                    
                    # Оценки по категориям
                    narrative_score=analysis_result.get('category_scores', {}).get('narrative', 0),
                    security_score=analysis_result.get('category_scores', {}).get('security', 0),
                    onchain_score=analysis_result.get('category_scores', {}).get('onchain', 0)
                )
                
                db.add(analysis)
                db.commit()
                db.refresh(analysis)
                
                self.logger.debug(f"✅ Сохранен анализ {token_data.get('symbol', 'UNKNOWN')} (ID={analysis.id})")
                return analysis.id
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Ошибка сохранения анализа: {e}")
            return -1
    
    def save_alert(self, session_id: int, analysis_id: int, alert_data: Dict[str, Any]) -> int:
        """Сохраняет созданный алерт. Возвращает alert_id."""
        try:
            with self.get_session() as db:
                alert = Alert(
                    token_address=alert_data['token_address'],
                    session_id=session_id,
                    analysis_id=analysis_id,
                    alert_timestamp=datetime.utcnow(),
                    
                    # Тип алерта и оценка
                    alert_type=alert_data.get('recommendation', 'UNKNOWN'),
                    final_score=alert_data.get('final_score', 0),
                    confidence_level=alert_data.get('confidence_level', 0.0),
                    
                    # Снимок рыночных данных
                    price_usd_at_alert=alert_data.get('price_usd'),
                    liquidity_usd_at_alert=alert_data.get('liquidity_usd'),
                    volume_24h_at_alert=alert_data.get('volume_24h')
                )
                
                db.add(alert)
                db.commit()
                db.refresh(alert)
                
                token_symbol = alert_data.get('token_symbol', 'UNKNOWN')
                self.logger.info(f"✅ Создан алерт {token_symbol} (ID={alert.id}, score={alert.final_score})")
                return alert.id
                
        except SQLAlchemyError as e:
            self.logger.error(f"❌ Ошибка сохранения алерта: {e}")
            return -1
