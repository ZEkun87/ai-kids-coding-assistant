#!/usr/bin/env python3
"""
验证PostgreSQL + PGVector迁移的完整性和正确性
"""

import logging
import sys
import os
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).parent / "backend"))

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)


class MigrationValidator:
    """迁移验证器"""

    def __init__(self):
        self.results = {"passed": [], "failed": [], "warnings": []}

    def add_result(self, status: str, message: str):
        """添加验证结果"""
        if status == "pass":
            self.results["passed"].append(message)
            logger.info(f"✅ {message}")
        elif status == "fail":
            self.results["failed"].append(message)
            logger.error(f"❌ {message}")
        elif status == "warn":
            self.results["warnings"].append(message)
            logger.warning(f"⚠️  {message}")

    def check_postgres_connection(self) -> bool:
        """检查PostgreSQL连接"""
        logger.info("\n📡 检查PostgreSQL连接...")
        try:
            from models.chat import engine, SessionLocal

            with engine.connect() as conn:
                result = conn.execute("SELECT version();")
                version = result.scalar()
                self.add_result("pass", f"PostgreSQL连接成功: {version[:50]}...")
                return True
        except Exception as e:
            self.add_result("fail", f"PostgreSQL连接失败: {e}")
            return False

    def check_tables(self) -> bool:
        """检查表存在"""
        logger.info("\n📊 检查数据库表...")
        try:
            from sqlalchemy import inspect
            from models.chat import engine

            inspector = inspect(engine)
            tables = inspector.get_table_names()

            required_tables = ["chat_records", "document_chunks", "embeddings"]
            found = []
            missing = []

            for table in required_tables:
                if table in tables:
                    found.append(table)
                    self.add_result("pass", f"表 '{table}' 存在")
                else:
                    missing.append(table)
                    self.add_result("fail", f"表 '{table}' 不存在")

            return len(missing) == 0
        except Exception as e:
            self.add_result("fail", f"表检查失败: {e}")
            return False

    def count_records(self) -> Tuple[int, int, int]:
        """统计记录数"""
        logger.info("\n📈 统计记录数...")
        try:
            from models.chat import SessionLocal, ChatRecord

            session = SessionLocal()

            chat_count = session.query(ChatRecord).count()
            self.add_result("pass", f"聊天记录: {chat_count} 条")

            # 尝试查询向量数据
            try:
                from sqlalchemy import text

                with session.bind.connect() as conn:
                    doc_result = conn.execute(
                        text("SELECT COUNT(*) FROM document_chunks")
                    )
                    doc_count = doc_result.scalar() or 0

                    emb_result = conn.execute(text("SELECT COUNT(*) FROM embeddings"))
                    emb_count = emb_result.scalar() or 0

                    self.add_result("pass", f"文档块: {doc_count} 条")
                    self.add_result("pass", f"向量嵌入: {emb_count} 条")

                    return chat_count, doc_count, emb_count
            except Exception as e:
                self.add_result("warn", f"无法查询向量表: {e}")
                return chat_count, 0, 0

        except Exception as e:
            self.add_result("fail", f"记录统计失败: {e}")
            return 0, 0, 0
        finally:
            session.close()

    def check_pgvector_extension(self) -> bool:
        """检查PGVector扩展"""
        logger.info("\n🔌 检查PGVector扩展...")
        try:
            from models.chat import SessionLocal
            from sqlalchemy import text

            session = SessionLocal()
            with session.bind.connect() as conn:
                result = conn.execute(
                    text("SELECT extname FROM pg_extension WHERE extname='vector'")
                )
                if result.scalar():
                    self.add_result("pass", "PGVector扩展已安装")
                    return True
                else:
                    self.add_result("warn", "PGVector扩展未安装（需要手动安装）")
                    return False
        except Exception as e:
            self.add_result("warn", f"无法检查PGVector扩展: {e}")
            return False
        finally:
            session.close()

    def check_old_data(self) -> dict:
        """检查旧数据的可用性"""
        logger.info("\n🗄️  检查旧数据...")
        old_data = {
            "sqlite": False,
            "chroma": False,
            "sqlite_count": 0,
            "chroma_count": 0,
        }

        # 检查SQLite
        sqlite_path = Path(__file__).parent / "backend" / "chat_history.db"
        if sqlite_path.exists():
            old_data["sqlite"] = True
            try:
                import sqlite3

                conn = sqlite3.connect(str(sqlite_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM chat_records")
                old_data["sqlite_count"] = cursor.fetchone()[0]
                conn.close()
                self.add_result(
                    "pass", f"旧SQLite数据库: {old_data['sqlite_count']} 条记录"
                )
            except Exception as e:
                self.add_result("warn", f"无法读取SQLite: {e}")
        else:
            self.add_result("warn", "旧SQLite数据库不存在（可能已删除）")

        # 检查Chroma
        chroma_path = Path(__file__).parent / "backend" / "chroma_db"
        if chroma_path.exists():
            old_data["chroma"] = True
            try:
                import chromadb

                client = chromadb.PersistentClient(path=str(chroma_path))
                for collection in client.list_collections():
                    old_data["chroma_count"] += collection.count()
                self.add_result(
                    "pass", f"旧Chroma数据库: {old_data['chroma_count']} 个文档"
                )
            except Exception as e:
                self.add_result("warn", f"无法读取Chroma: {e}")
        else:
            self.add_result("warn", "旧Chroma数据库不存在（可能已删除）")

        return old_data

    def check_performance(self) -> bool:
        """性能基准测试"""
        logger.info("\n⚡ 性能基准测试...")
        try:
            from models.chat import SessionLocal, ChatRecord
            import time

            session = SessionLocal()

            # 查询性能
            start = time.time()
            records = session.query(ChatRecord).limit(100).all()
            elapsed = (time.time() - start) * 1000

            if elapsed < 100:  # < 100ms
                self.add_result("pass", f"查询性能: {elapsed:.2f}ms (优秀)")
            elif elapsed < 500:
                self.add_result("pass", f"查询性能: {elapsed:.2f}ms (良好)")
            else:
                self.add_result("warn", f"查询性能: {elapsed:.2f}ms (需要优化)")

            session.close()
            return True
        except Exception as e:
            self.add_result("fail", f"性能测试失败: {e}")
            return False

    def check_environment(self) -> bool:
        """检查环境配置"""
        logger.info("\n🔧 检查环境配置...")
        checks_passed = True

        # 检查DATABASE_URL
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            self.add_result("pass", f"DATABASE_URL已设置: {db_url[:40]}...")
        else:
            self.add_result("fail", "DATABASE_URL未设置")
            checks_passed = False

        # 检查DASHSCOPE_API_KEY
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if api_key:
            self.add_result("pass", "DASHSCOPE_API_KEY已设置")
        else:
            self.add_result("warn", "DASHSCOPE_API_KEY未设置（向量功能受限）")

        # 检查依赖
        try:
            import psycopg

            self.add_result("pass", f"psycopg: {psycopg.__version__}")
        except ImportError:
            self.add_result("fail", "psycopg未安装")
            checks_passed = False

        try:
            import pgvector

            self.add_result("pass", "pgvector已安装")
        except ImportError:
            self.add_result("warn", "pgvector未安装（可选）")

        return checks_passed

    def generate_report(self) -> str:
        """生成验证报告"""
        total = (
            len(self.results["passed"])
            + len(self.results["failed"])
            + len(self.results["warnings"])
        )
        passed = len(self.results["passed"])
        failed = len(self.results["failed"])
        warnings = len(self.results["warnings"])

        success_rate = (passed / total * 100) if total > 0 else 0

        report = f"""
╔════════════════════════════════════════════════════════════╗
║    PostgreSQL + PGVector 迁移完整性验证报告                 ║
╚════════════════════════════════════════════════════════════╝

📊 验证结果:
   ✅ 通过: {passed}/{total}
   ❌ 失败: {failed}/{total}
   ⚠️ 警告: {warnings}/{total}
   📈 成功率: {success_rate:.1f}%

"""

        if failed > 0:
            report += "❌ 失败项:\n"
            for item in self.results["failed"]:
                report += f"   • {item}\n"
            report += "\n"

        if warnings > 0:
            report += "⚠️ 警告项:\n"
            for item in self.results["warnings"]:
                report += f"   • {item}\n"
            report += "\n"

        if failed == 0:
            report += "✅ 所有关键检查已通过！迁移可以继续。\n"
        else:
            report += "❌ 存在失败项，请先解决。\n"

        report += """
╔════════════════════════════════════════════════════════════╗
"""
        return report

    def run_all_checks(self) -> bool:
        """运行所有检查"""
        self.check_environment()

        if not self.check_postgres_connection():
            logger.error("无法连接到PostgreSQL，停止验证")
            return False

        self.check_tables()
        self.check_pgvector_extension()

        chat_count, doc_count, emb_count = self.count_records()
        old_data = self.check_old_data()

        # 验证迁移
        if old_data["sqlite"] and old_data["sqlite_count"] > 0:
            if chat_count == old_data["sqlite_count"]:
                self.add_result("pass", "✓ 聊天记录迁移完整")
            else:
                self.add_result(
                    "warn",
                    f"聊天记录数不匹配: 旧={old_data['sqlite_count']}, 新={chat_count}",
                )

        if old_data["chroma"] and old_data["chroma_count"] > 0:
            if doc_count >= old_data["chroma_count"] * 0.9:  # 允许10%的误差
                self.add_result("pass", "✓ 向量文档迁移基本完整")
            else:
                self.add_result(
                    "warn",
                    f"向量文档数不匹配: 旧={old_data['chroma_count']}, 新={doc_count}",
                )

        self.check_performance()

        return len(self.results["failed"]) == 0


def main():
    """主函数"""
    validator = MigrationValidator()
    success = validator.run_all_checks()

    print(validator.generate_report())

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
