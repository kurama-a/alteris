"""
Tests pour le module de performance.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.performance import (
    PaginatedResult,
    QueryOptimizer,
    PerformanceMetrics,
    get_memory_stats,
    check_memory_threshold,
)


class TestPaginatedResult:
    """Tests pour PaginatedResult."""
    
    def test_create_first_page(self):
        """Création d'un résultat paginé - première page."""
        items = [{"id": i} for i in range(20)]
        result = PaginatedResult.create(items=items, total=100, page=1, page_size=20)
        
        assert result.total == 100
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_pages == 5
        assert result.has_next is True
        assert result.has_previous is False
        assert len(result.items) == 20
    
    def test_create_middle_page(self):
        """Création d'un résultat paginé - page intermédiaire."""
        items = [{"id": i} for i in range(20)]
        result = PaginatedResult.create(items=items, total=100, page=3, page_size=20)
        
        assert result.page == 3
        assert result.has_next is True
        assert result.has_previous is True
    
    def test_create_last_page(self):
        """Création d'un résultat paginé - dernière page."""
        items = [{"id": i} for i in range(10)]
        result = PaginatedResult.create(items=items, total=50, page=5, page_size=10)
        
        assert result.page == 5
        assert result.total_pages == 5
        assert result.has_next is False
        assert result.has_previous is True
    
    def test_create_single_page(self):
        """Création d'un résultat paginé - page unique."""
        items = [{"id": i} for i in range(5)]
        result = PaginatedResult.create(items=items, total=5, page=1, page_size=20)
        
        assert result.total_pages == 1
        assert result.has_next is False
        assert result.has_previous is False
    
    def test_to_dict(self):
        """Conversion en dictionnaire."""
        items = [{"id": 1}, {"id": 2}]
        result = PaginatedResult.create(items=items, total=10, page=1, page_size=2)
        
        dict_result = result.to_dict()
        
        assert "items" in dict_result
        assert "pagination" in dict_result
        assert dict_result["pagination"]["total"] == 10
        assert dict_result["pagination"]["page"] == 1


class TestQueryOptimizer:
    """Tests pour QueryOptimizer."""
    
    def test_build_text_search_query_single_field(self):
        """Requête de recherche textuelle - champ unique."""
        query = QueryOptimizer.build_text_search_query("john", ["name"])
        
        assert "name" in query
        assert query["name"]["$regex"] == "john"
        assert query["name"]["$options"] == "i"
    
    def test_build_text_search_query_multiple_fields(self):
        """Requête de recherche textuelle - champs multiples."""
        query = QueryOptimizer.build_text_search_query("test", ["name", "email"])
        
        assert "$or" in query
        assert len(query["$or"]) == 2
    
    def test_build_text_search_query_empty(self):
        """Requête de recherche textuelle - terme vide."""
        query = QueryOptimizer.build_text_search_query("", ["name"])
        assert query == {}
    
    def test_build_text_search_query_escapes_regex(self):
        """Requête de recherche textuelle - échappement regex."""
        query = QueryOptimizer.build_text_search_query("test.user+tag", ["name"])
        
        # Les caractères spéciaux doivent être échappés
        assert r"\." in query["name"]["$regex"]
        assert r"\+" in query["name"]["$regex"]
    
    def test_build_date_range_query_both_dates(self):
        """Requête de plage de dates - les deux dates."""
        from datetime import datetime
        
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        
        query = QueryOptimizer.build_date_range_query("created_at", start, end)
        
        assert "created_at" in query
        assert query["created_at"]["$gte"] == start
        assert query["created_at"]["$lte"] == end
    
    def test_build_date_range_query_start_only(self):
        """Requête de plage de dates - date de début uniquement."""
        from datetime import datetime
        
        start = datetime(2024, 1, 1)
        
        query = QueryOptimizer.build_date_range_query("created_at", start_date=start)
        
        assert query["created_at"]["$gte"] == start
        assert "$lte" not in query["created_at"]
    
    def test_build_date_range_query_end_only(self):
        """Requête de plage de dates - date de fin uniquement."""
        from datetime import datetime
        
        end = datetime(2024, 12, 31)
        
        query = QueryOptimizer.build_date_range_query("created_at", end_date=end)
        
        assert query["created_at"]["$lte"] == end
        assert "$gte" not in query["created_at"]
    
    def test_build_date_range_query_no_dates(self):
        """Requête de plage de dates - aucune date."""
        query = QueryOptimizer.build_date_range_query("created_at")
        assert query == {}
    
    def test_projection_for_list(self):
        """Projection pour les listes."""
        projection = QueryOptimizer.projection_for_list(["id", "name", "email"])
        
        assert projection == {"id": 1, "name": 1, "email": 1}


class TestPerformanceMetrics:
    """Tests pour PerformanceMetrics."""
    
    def test_record_request_time(self):
        """Enregistrement du temps de requête."""
        metrics = PerformanceMetrics()
        
        metrics.record_request_time(10.5)
        metrics.record_request_time(20.3)
        metrics.record_request_time(15.0)
        
        stats = metrics.get_stats()
        
        assert stats["count"] == 3
        assert stats["min_ms"] == 10.5
        assert stats["max_ms"] == 20.3
    
    def test_get_stats_empty(self):
        """Statistiques vides."""
        metrics = PerformanceMetrics()
        stats = metrics.get_stats()
        
        assert "message" in stats
    
    def test_get_stats_average(self):
        """Calcul de la moyenne."""
        metrics = PerformanceMetrics()
        
        for t in [10, 20, 30]:
            metrics.record_request_time(t)
        
        stats = metrics.get_stats()
        assert stats["avg_ms"] == 20.0
    
    def test_get_stats_percentiles(self):
        """Calcul des percentiles."""
        metrics = PerformanceMetrics()
        
        # Ajouter suffisamment de données pour les percentiles
        for i in range(100):
            metrics.record_request_time(float(i))
        
        stats = metrics.get_stats()
        
        assert stats["p50_ms"] == 50.0
        assert stats["p95_ms"] is not None
        assert stats["p99_ms"] is not None
    
    def test_max_samples_limit(self):
        """Limite du nombre d'échantillons."""
        metrics = PerformanceMetrics()
        metrics._max_samples = 100
        
        # Ajouter plus que la limite
        for i in range(150):
            metrics.record_request_time(float(i))
        
        # Vérifier que seuls les derniers sont gardés
        assert len(metrics._request_times) <= 100


class TestMemoryStats:
    """Tests pour les statistiques mémoire."""
    
    def test_get_memory_stats(self):
        """Récupération des stats mémoire."""
        stats = get_memory_stats()
        
        # Les stats doivent exister (même si psutil n'est pas installé)
        assert hasattr(stats, 'rss_mb')
        assert hasattr(stats, 'gc_counts')
        assert hasattr(stats, 'objects_count')
    
    def test_check_memory_threshold(self):
        """Vérification du seuil mémoire."""
        exceeded, current_mb = check_memory_threshold()
        
        # Le résultat doit être un tuple bool, float
        assert isinstance(exceeded, bool)
        assert isinstance(current_mb, (int, float))


class TestPaginateCursor:
    """Tests pour la pagination de curseur MongoDB."""
    
    @pytest.mark.asyncio
    async def test_paginate_cursor_basic(self):
        """Pagination basique avec curseur mock."""
        from common.performance import paginate_cursor
        
        # Mock de la collection MongoDB
        mock_collection = MagicMock()
        mock_collection.count_documents = AsyncMock(return_value=50)
        
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[{"id": i} for i in range(10)])
        
        mock_collection.find = MagicMock(return_value=mock_cursor)
        
        result = await paginate_cursor(
            mock_collection,
            query={"status": "active"},
            page=2,
            page_size=10
        )
        
        assert result.total == 50
        assert result.page == 2
        assert result.page_size == 10
        assert result.total_pages == 5
        assert len(result.items) == 10
        
        # Vérifier les appels
        mock_cursor.skip.assert_called_once_with(10)  # (page-1) * page_size
        mock_cursor.limit.assert_called_once_with(10)


class TestCursorPagination:
    """Tests pour la pagination par curseur."""
    
    @pytest.mark.asyncio
    async def test_cursor_pagination_first_page(self):
        """Pagination par curseur - première page."""
        from common.performance import cursor_pagination
        
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": f"id{i}"} for i in range(11)  # limit + 1 pour savoir s'il y a une page suivante
        ])
        
        mock_collection.find = MagicMock(return_value=mock_cursor)
        
        items, next_cursor = await cursor_pagination(
            mock_collection,
            query={},
            limit=10
        )
        
        assert len(items) == 10
        assert next_cursor == "id9"  # Dernier élément de la page
    
    @pytest.mark.asyncio
    async def test_cursor_pagination_last_page(self):
        """Pagination par curseur - dernière page."""
        from common.performance import cursor_pagination
        
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": f"id{i}"} for i in range(5)  # Moins que limit
        ])
        
        mock_collection.find = MagicMock(return_value=mock_cursor)
        
        items, next_cursor = await cursor_pagination(
            mock_collection,
            query={},
            limit=10
        )
        
        assert len(items) == 5
        assert next_cursor is None  # Pas de page suivante
