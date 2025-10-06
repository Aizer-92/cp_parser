"""
Менеджер базы данных для умного парсера коммерческих предложений
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
import logging
from typing import Optional, List

from .models import Base, Project, Product, PriceOffer, ProductImage

class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Инициализация менеджера базы данных
        
        Args:
            database_url: URL базы данных. Если None, используется SQLite
        """
        if database_url is None:
            # По умолчанию используем SQLite в папке database
            db_path = Path(__file__).parent / "commercial_proposals.db"
            db_path.parent.mkdir(exist_ok=True)
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,  # Установить True для отладки SQL
            pool_pre_ping=True
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self.logger = logging.getLogger(__name__)
    
    def create_tables(self):
        """Создание всех таблиц в базе данных"""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Таблицы базы данных созданы успешно")
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка создания таблиц: {e}")
            raise
    
    def drop_tables(self):
        """Удаление всех таблиц (ОСТОРОЖНО!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            self.logger.info("Таблицы базы данных удалены")
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка удаления таблиц: {e}")
            raise
    
    def get_session(self) -> Session:
        """Получение сессии базы данных"""
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Проверка доступности базы данных"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.logger.error(f"Ошибка подключения к БД: {e}")
            return False


class ProjectService:
    """Сервис для работы с проектами"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_project(self, **kwargs) -> Project:
        """Создание нового проекта"""
        with self.db_manager.get_session() as session:
            project = Project(**kwargs)
            session.add(project)
            session.commit()
            session.refresh(project)
            self.logger.info(f"Создан проект: {project.project_name} (ID: {project.id})")
            return project
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """Получение проекта по ID"""
        with self.db_manager.get_session() as session:
            return session.query(Project).filter(Project.id == project_id).first()
    
    def get_project_by_file_name(self, file_name: str) -> Optional[Project]:
        """Получение проекта по имени файла"""
        with self.db_manager.get_session() as session:
            return session.query(Project).filter(Project.file_name == file_name).first()
    
    def get_all_projects(self) -> List[Project]:
        """Получение всех проектов"""
        with self.db_manager.get_session() as session:
            return session.query(Project).all()
    
    def get_projects_by_status(self, status: str) -> List[Project]:
        """Получение проектов по статусу"""
        with self.db_manager.get_session() as session:
            return session.query(Project).filter(Project.parsing_status == status).all()
    
    def update_project_status(self, project_id: int, status: str, **kwargs):
        """Обновление статуса проекта"""
        with self.db_manager.get_session() as session:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                project.parsing_status = status
                for key, value in kwargs.items():
                    if hasattr(project, key):
                        setattr(project, key, value)
                session.commit()
                self.logger.info(f"Обновлен статус проекта {project_id}: {status}")


class ProductService:
    """Сервис для работы с товарами"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_product(self, **kwargs) -> Product:
        """Создание нового товара"""
        with self.db_manager.get_session() as session:
            product = Product(**kwargs)
            session.add(product)
            session.commit()
            session.refresh(product)
            self.logger.info(f"Создан товар: {product.name} (ID: {product.id})")
            return product
    
    def get_products_by_project(self, project_id: int) -> List[Product]:
        """Получение товаров проекта"""
        with self.db_manager.get_session() as session:
            return session.query(Product).filter(Product.project_id == project_id).all()
    
    def search_products(self, query: str) -> List[Product]:
        """Поиск товаров по названию"""
        with self.db_manager.get_session() as session:
            return session.query(Product).filter(
                Product.name.contains(query)
            ).all()
    
    def get_product_by_table_id_and_row(self, table_id: str, row_number: int) -> Optional[Product]:
        """Получение товара по table_id и номеру строки"""
        with self.db_manager.get_session() as session:
            return session.query(Product).filter(
                Product.table_id == table_id,
                Product.row_number == row_number
            ).first()
    
    def get_products_by_project_id(self, project_id: int) -> List[Product]:
        """Получение товаров по project_id"""
        with self.db_manager.get_session() as session:
            return session.query(Product).filter(Product.project_id == project_id).all()
    
    def get_all_products(self) -> List[Product]:
        """Получение всех товаров"""
        with self.db_manager.get_session() as session:
            return session.query(Product).all()
    
    def update_product_row_end(self, product_id: int, row_end: int):
        """Обновление конечной строки товара"""
        with self.db_manager.get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                product.row_number_end = row_end
                session.commit()
                self.logger.info(f"Обновлена конечная строка товара {product_id}: {row_end}")


class PriceOfferService:
    """Сервис для работы с ценовыми предложениями"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_price_offer(self, **kwargs) -> PriceOffer:
        """Создание ценового предложения"""
        with self.db_manager.get_session() as session:
            offer = PriceOffer(**kwargs)
            session.add(offer)
            session.commit()
            session.refresh(offer)
            return offer
    
    def get_offers_by_product(self, product_id: int) -> List[PriceOffer]:
        """Получение ценовых предложений товара"""
        with self.db_manager.get_session() as session:
            return session.query(PriceOffer).filter(
                PriceOffer.product_id == product_id
            ).order_by(PriceOffer.quantity).all()
    
    def get_price_offers_by_product_id(self, product_id: int) -> List[PriceOffer]:
        """Получение ценовых предложений по product_id"""
        with self.db_manager.get_session() as session:
            return session.query(PriceOffer).filter(PriceOffer.product_id == product_id).all()
    
    def get_all_price_offers(self) -> List[PriceOffer]:
        """Получение всех ценовых предложений"""
        with self.db_manager.get_session() as session:
            return session.query(PriceOffer).all()
    
    def get_price_offer_by_table_id_and_position(self, table_id: str, row_position: str) -> Optional[PriceOffer]:
        """Получение ценового предложения по table_id и позиции"""
        with self.db_manager.get_session() as session:
            return session.query(PriceOffer).filter(
                PriceOffer.table_id == table_id,
                PriceOffer.row_position == row_position
            ).first()
    
    def get_price_offer_by_product_and_route(self, product_id: int, route: str, quantity: int) -> Optional[PriceOffer]:
        """Получение ценового предложения по product_id, маршруту и тиражу"""
        with self.db_manager.get_session() as session:
            return session.query(PriceOffer).filter(
                PriceOffer.product_id == product_id,
                PriceOffer.route == route,
                PriceOffer.quantity == quantity
            ).first()
    
    def get_offer_by_product_and_route(self, product_id: int, route: str, quantity: int) -> Optional[PriceOffer]:
        """Алиас для get_price_offer_by_product_and_route (для совместимости с парсером)"""
        return self.get_price_offer_by_product_and_route(product_id, route, quantity)
    
    def create_offer(self, **kwargs) -> PriceOffer:
        """Алиас для create_price_offer (для совместимости с парсером)"""
        return self.create_price_offer(**kwargs)


class ImageService:
    """Сервис для работы с изображениями"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_image(self, **kwargs) -> ProductImage:
        """Создание записи об изображении"""
        with self.db_manager.get_session() as session:
            image = ProductImage(**kwargs)
            session.add(image)
            session.commit()
            session.refresh(image)
            return image
    
    def get_images_by_product(self, product_id: int) -> List[ProductImage]:
        """Получение изображений товара"""
        with self.db_manager.get_session() as session:
            return session.query(ProductImage).filter(
                ProductImage.product_id == product_id
            ).order_by(ProductImage.display_order).all()
    
    def get_images_by_product_id(self, product_id: int) -> List[ProductImage]:
        """Получение изображений по product_id"""
        with self.db_manager.get_session() as session:
            return session.query(ProductImage).filter(ProductImage.product_id == product_id).all()
    
    def get_all_images(self) -> List[ProductImage]:
        """Получение всех изображений"""
        with self.db_manager.get_session() as session:
            return session.query(ProductImage).all()
    
    def get_unlinked_images_by_project_id(self, project_id: int) -> List[ProductImage]:
        """Получение непривязанных изображений по project_id через table_id"""
        with self.db_manager.get_session() as session:
            # Получаем table_id проекта
            project = session.query(Project).filter(Project.id == project_id).first()
            if not project or not project.table_id:
                return []
            
            return session.query(ProductImage).filter(
                ProductImage.table_id == project.table_id,
                ProductImage.product_id.is_(None)
            ).all()
    
    def get_image_by_table_id_and_position(self, table_id: str, cell_position: str) -> Optional[ProductImage]:
        """Получение изображения по table_id и позиции ячейки"""
        with self.db_manager.get_session() as session:
            return session.query(ProductImage).filter(
                ProductImage.table_id == table_id,
                ProductImage.cell_position == cell_position
            ).first()


# Singleton экземпляр менеджера БД
db_manager = DatabaseManager()

# Экземпляры сервисов
project_service = ProjectService(db_manager)
product_service = ProductService(db_manager)
price_offer_service = PriceOfferService(db_manager)
image_service = ImageService(db_manager)
