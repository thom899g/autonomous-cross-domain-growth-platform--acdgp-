"""
Firebase manager for ACDGP with connection pooling and error recovery.
Architecture Choice: Singleton pattern ensures single Firebase connection
across the entire application, preventing connection leaks.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.client import Client as FirestoreClient
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import Optional, Dict, Any, List
import logging
from contextlib import contextmanager
import time
from datetime import datetime
from config import CONFIG

logger = logging.getLogger(__name__)

class FirebaseManager:
    """Manages Firebase connections with automatic reconnection"""
    
    _instance: Optional['FirebaseManager'] = None
    _app = None
    _db: Optional[FirestoreClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Firebase connection with error handling"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(CONFIG.firebase.credentials_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': CONFIG.firebase.project_id
                })
                logger.info(f"Firebase initialized for project: {CONFIG.firebase.project_id}")
            self._db = firestore.client()
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            raise
    
    @property
    def db(self) -> FirestoreClient:
        """Lazy-loaded Firestore client"""
        if self._db is None:
            self._initialize()
        return self._db
    
    @contextmanager
    def get_batch_writer(self, batch_size: int = 500):
        """Context manager for batch writes with automatic commit"""
        batch = self.db.batch()
        operations_count = 0
        
        try:
            yield batch
            if operations_count > 0:
                batch.commit()
                logger.debug(f"Committed batch with {operations_count} operations")
        except Exception as e:
            logger.error(f"Batch operation failed: {str(e)}")
            raise
    
    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Safe document retrieval with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc = doc_ref.get()
                if doc.exists:
                    return {**doc.to_dict(), 'id': doc.id}
                return None
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to get document {doc_id} after {max_retries} attempts: {str(e)}")
                    raise
                time.sleep(2 ** attempt)
    
    def query_collection(self, collection: str, filters: Optional[List[Dict]] = None, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Execute Firestore query with filters"""
        try:
            query = self.db.collection(collection)
            
            if filters:
                for filter_dict in filters:
                    field = filter_dict.get('