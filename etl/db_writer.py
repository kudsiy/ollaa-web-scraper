"""
Database writer for inserting normalized listings into Ollaa PostgreSQL.
"""
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import execute_values

from config import get_config


logger = logging.getLogger(__name__)


class DBWriter:
    """
    Handles database operations for the Ollaa web scraper.
    Inserts normalized listings into the web_scraped_listings table.
    """
    
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        self.config = get_config()
        self.db_config = db_config or {}
        self._connection = None
        
    def _get_connection_params(self) -> Dict[str, Any]:
        """Get database connection parameters."""
        return {
            "host": self.db_config.get("host", self.config.db.host),
            "port": self.db_config.get("port", self.config.db.port),
            "database": self.db_config.get("database", self.config.db.database),
            "user": self.db_config.get("user", self.config.db.user),
            "password": self.db_config.get("password", self.config.db.password),
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connection."""
        conn = None
        try:
            conn = psycopg2.connect(**self._get_connection_params())
            yield conn
        finally:
            if conn:
                conn.close()
    
    def init_database(self) -> bool:
        """
        Initialize the database schema if not exists.
        
        Returns:
            True if successful
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS web_scraped_listings (
                            id SERIAL PRIMARY KEY,
                            source_url TEXT,
                            source_name VARCHAR(100),
                            title TEXT NOT NULL,
                            description TEXT,
                            price DECIMAL(15,2),
                            price_currency VARCHAR(10) DEFAULT 'ETB',
                            property_type VARCHAR(50),
                            location VARCHAR(255),
                            area_sqm DECIMAL(10,2),
                            bedrooms INTEGER,
                            bathrooms INTEGER,
                            images TEXT[],
                            posted_date TIMESTAMP,
                            closing_date TIMESTAMP,
                            listing_type VARCHAR(20) DEFAULT 'sale',
                            content_hash VARCHAR(64) UNIQUE,
                            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            raw_data JSONB,
                            CONSTRAINT unique_content_hash UNIQUE (content_hash)
                        )
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_source_name 
                        ON web_scraped_listings(source_name)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_listing_type 
                        ON web_scraped_listings(listing_type)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_scraped_at 
                        ON web_scraped_listings(scraped_at)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_location 
                        ON web_scraped_listings(location)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_content_hash 
                        ON web_scraped_listings(content_hash)
                    """)
                    
                    conn.commit()
                    logger.info("Database schema initialized successfully")
                    return True
                    
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    
    def insert_listings(self, listings: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Insert multiple listings into the database.
        
        Args:
            listings: List of normalized listing dictionaries
            
        Returns:
            Dictionary with insert statistics
        """
        if not listings:
            return {"inserted": 0, "skipped": 0, "errors": 0}
            
        stats = {"inserted": 0, "skipped": 0, "errors": 0}
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for listing in listings:
                        try:
                            result = self._insert_single(cursor, listing)
                            if result == "inserted":
                                stats["inserted"] += 1
                            elif result == "skipped":
                                stats["skipped"] += 1
                        except Exception as e:
                            logger.error(f"Error inserting listing: {e}")
                            stats["errors"] += 1
                            
                conn.commit()
                
        except Exception as e:
            logger.error(f"Database insert error: {e}")
            stats["errors"] = len(listings)
            
        return stats
    
    def _insert_single(self, cursor, listing: Dict[str, Any]) -> str:
        """
        Insert a single listing.
        
        Args:
            cursor: Database cursor
            listing: Normalized listing dictionary
            
        Returns:
            "inserted", "skipped", or raises exception
        """
        content_hash = listing.get("content_hash")
        
        if content_hash:
            cursor.execute("""
                SELECT id FROM web_scraped_listings 
                WHERE content_hash = %s
            """, (content_hash,))
            
            if cursor.fetchone():
                return "skipped"
        
        cursor.execute("""
            INSERT INTO web_scraped_listings (
                source_url, source_name, title, description, price, 
                price_currency, property_type, location, area_sqm, 
                bedrooms, bathrooms, images, posted_date, closing_date,
                listing_type, content_hash, scraped_at, raw_data
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (content_hash) DO NOTHING
        """, (
            listing.get("source_url"),
            listing.get("source_name"),
            listing.get("title"),
            listing.get("description"),
            listing.get("price"),
            listing.get("price_currency", "ETB"),
            listing.get("property_type"),
            listing.get("location"),
            listing.get("area_sqm"),
            listing.get("bedrooms"),
            listing.get("bathrooms"),
            listing.get("images"),
            listing.get("posted_date"),
            listing.get("closing_date"),
            listing.get("listing_type", "sale"),
            content_hash,
            listing.get("scraped_at", datetime.utcnow()),
            json.dumps(listing.get("raw_data", {})) if listing.get("raw_data") else None
        ))
        
        if cursor.rowcount > 0:
            return "inserted"
        return "skipped"
    
    def insert_batch(self, listings: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, int]:
        """
        Insert listings in batches for better performance.
        
        Args:
            listings: List of normalized listing dictionaries
            batch_size: Number of listings per batch
            
        Returns:
            Dictionary with insert statistics
        """
        if not listings:
            return {"inserted": 0, "skipped": 0, "errors": 0}
            
        stats = {"inserted": 0, "skipped": 0, "errors": 0}
        
        for i in range(0, len(listings), batch_size):
            batch = listings[i:i + batch_size]
            batch_stats = self.insert_listings(batch)
            stats["inserted"] += batch_stats["inserted"]
            stats["skipped"] += batch_stats["skipped"]
            stats["errors"] += batch_stats["errors"]
            
        return stats
    
    def get_recent_listings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent listings from database.
        
        Args:
            limit: Maximum number of listings to return
            
        Returns:
            List of listing dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM web_scraped_listings 
                        ORDER BY scraped_at DESC 
                        LIMIT %s
                    """, (limit,))
                    
                    columns = [desc[0] for desc in cursor.description]
                    results = []
                    
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
                        
                    return results
                    
        except Exception as e:
            logger.error(f"Error fetching recent listings: {e}")
            return []
    
    def get_listings_by_source(self, source_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get listings by source.
        
        Args:
            source_name: Name of the source
            limit: Maximum number of listings to return
            
        Returns:
            List of listing dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM web_scraped_listings 
                        WHERE source_name = %s
                        ORDER BY scraped_at DESC 
                        LIMIT %s
                    """, (source_name, limit))
                    
                    columns = [desc[0] for desc in cursor.description]
                    results = []
                    
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
                        
                    return results
                    
        except Exception as e:
            logger.error(f"Error fetching listings by source: {e}")
            return []
    
    def get_listing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about listings in database.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(DISTINCT source_name) as sources,
                            COUNT(DISTINCT location) as locations,
                            AVG(price) as avg_price,
                            MIN(scraped_at) as first_scraped,
                            MAX(scraped_at) as last_scraped
                        FROM web_scraped_listings
                    """)
                    row = cursor.fetchone()
                    
                    stats = {
                        "total_listings": row[0],
                        "total_sources": row[1],
                        "total_locations": row[2],
                        "avg_price": float(row[3]) if row[3] else 0,
                        "first_scraped": row[4],
                        "last_scraped": row[5]
                    }
                    
                    cursor.execute("""
                        SELECT source_name, COUNT(*) as count
                        FROM web_scraped_listings
                        GROUP BY source_name
                        ORDER BY count DESC
                    """)
                    
                    stats["by_source"] = [
                        {"source": row[0], "count": row[1]}
                        for row in cursor.fetchall()
                    ]
                    
                    cursor.execute("""
                        SELECT listing_type, COUNT(*) as count
                        FROM web_scraped_listings
                        GROUP BY listing_type
                    """)
                    
                    stats["by_type"] = [
                        {"type": row[0], "count": row[1]}
                        for row in cursor.fetchall()
                    ]
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"Error fetching listing stats: {e}")
            return {}
    
    def delete_old_listings(self, days: int = 90) -> int:
        """
        Delete listings older than specified days.
        
        Args:
            days: Delete listings older than this many days
            
        Returns:
            Number of deleted listings
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM web_scraped_listings 
                        WHERE scraped_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    """, (days,))
                    
                    deleted = cursor.rowcount
                    conn.commit()
                    
                    logger.info(f"Deleted {deleted} old listings")
                    return deleted
                    
        except Exception as e:
            logger.error(f"Error deleting old listings: {e}")
            return 0