import sys
from unittest.mock import MagicMock

# 全局 Mock 避免導入時報報錯
mock_psycopg2 = MagicMock()
mock_psycopg2.extras.RealDictCursor = MagicMock()
mock_psycopg2.pool.ThreadedConnectionPool = MagicMock()

sys.modules["tvscreener"] = MagicMock()
sys.modules["psycopg2"] = mock_psycopg2
sys.modules["psycopg2.extras"] = mock_psycopg2.extras
sys.modules["psycopg2.pool"] = mock_psycopg2.pool
